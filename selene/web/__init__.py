# -*- coding: utf-8 *-*
import functools
import tornado.escape
import tornado.gen
import tornado.web
import urllib

from motor import Op
from selene import helpers
from tornado.options import options


def authenticated_async(f):

    @functools.wraps(f)
    @tornado.gen.engine
    def wrapper(self, *args, **kwargs):
        self._auto_finish = False
        self.current_user = yield tornado.gen.Task(self.get_current_user_async)
        if not self.current_user:
            self.redirect(self.get_login_url() + '?' +
                urllib.urlencode({'next': self.request.uri}))
        else:
            f(self, *args, **kwargs)
    return wrapper


def redirect_authenticated_user(f):

    @functools.wraps(f)
    @tornado.gen.engine
    def wrapper(self, *args, **kwargs):
        self._auto_finish = False
        self.current_user = yield tornado.gen.Task(self.get_current_user_async)
        if self.current_user:
            self.redirect(self.reverse_url('home'))
        else:
            f(self, *args, **kwargs)
    return wrapper


def validate_form(form_class, template, **params):

    def decorator(f):

        @functools.wraps(f)
        @tornado.gen.engine
        def wrapper(self, *args, **kwargs):
            self.form = form_class(self.request.arguments,
                                   locale_code=self.locale.code, **params)
            if not self.form.validate():
                self.render(template, message=self.form.errors, form=self.form)
            else:
                f(self, *args, **kwargs)
        return wrapper
    return decorator


class BaseHandler(tornado.web.RequestHandler):

    current_user = None

    @property
    def db(self):
        return self.application.db

    @property
    def smtp(self):
        return self.application.smtp

    @tornado.gen.engine
    def get_current_user_async(self, callback):
        email = self.get_secure_cookie("current_user") or False
        if not email:
            callback(None)
        else:
            callback((yield Op(self.db.users.find_one, {"email": email})))

    @tornado.gen.engine
    @tornado.web.asynchronous
    def render(self, template_name, **kwargs):
        @tornado.gen.engine
        def find_post(comment, callback):
            comment['post'] = yield Op(self.db.posts.find_one, {'_id':
                comment['postid']})
            callback(comment)

        posts = yield Op(self.db.posts.find({'status': 'published'}).sort(
            'date', -1).limit(options.recent_posts_limit).to_list)
        comments = yield Op(self.db.comments.find().sort('date', -1).limit(
            options.recent_comments_limit).to_list)
        for comment in comments:
            find_post(comment, (yield tornado.gen.Callback(comment['_id'])))
        comments = yield tornado.gen.WaitAll([comment['_id'] for comment in
            comments])
        tags = yield Op(self.db.posts.aggregate, [
            {'$match': {'status': 'published'}},
            {'$unwind': '$tags'},
            {'$group': {'_id': '$tags', 'sum': {'$sum': 1}}},
            {'$limit': options.tag_cloud_limit}
        ])
        kwargs.update({
            'current_user':
                (yield tornado.gen.Task(self.get_current_user_async)),
            'url_path': helpers.Url(self.request.uri).path,
            '_next': self.get_argument('next', ''),
            '_posts': posts,
            '_comments': comments,
            '_tags': tags['result']
        })
        super(BaseHandler, self).render(template_name, **kwargs)


class ErrorHandler(BaseHandler):

    def __init__(self, application, request, status_code):
        BaseHandler.__init__(self, application, request)
        self.set_status(status_code)

    def write_error(self, status_code, **kwargs):
        if status_code in [403, 404, 500, 503]:
            self.require_setting("template_path")
            self.render('%d.html' % status_code)
        else:
            super(BaseHandler, self).write_error(status_code, **kwargs)

    def prepare(self):
        raise tornado.web.HTTPError(self._status_code)