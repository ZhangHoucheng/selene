# -*- coding: utf-8 *-*
import base64
import os
import tornado.options


def setup_options(path):
    #HTTP Server
    tornado.options.define("port", default=8081, type=int, help='Server port')

    #Database
    tornado.options.define("db_uri", default="mongodb://localhost:27017",
        type=str, help='MongoDB database URI')
    tornado.options.define("db_name", default="selene", type=str,
        help='MongoDB database name')

    #SMTP
    tornado.options.define('smtp_host', default='smtp.gmail.com', type=str,
        help='SMTP server host')
    tornado.options.define('smtp_port', default=587, type=int,
        help='SMTP server port')
    tornado.options.define('smtp_username', type=str, help='SMTP user')
    tornado.options.define('smtp_password', type=str, help='SMTP password')
    tornado.options.define('smtp_use_tls', default=True, type=bool,
        help='SMTP use TLS flag')

    #Blog
    tornado.options.define('base_url', default='http://localhost:8081',
        type=str, help='Base URL')
    tornado.options.define('title', default='Selene', type=str,
        help='Blog title')
    tornado.options.define('slogan', default=('A simple CMS for blogging built'
        ' with Tornado and MongoDB'), type=str, help='Blog slogan')
    tornado.options.define('default_language', default='en_US', type=str,
        help='Default language')

    #Application settings
    tornado.options.define('cookie_secret', default='', type=str)
    tornado.options.define("debug", default=True, type=bool, help=(
        'Turn on autoreload, log to stderr only'))
    tornado.options.define('theme_path', default='theme', type=str,
        help='Theme directory')
    tornado.options.define('static_url_prefix', default=None, type=str,
        help='Static files prefix')

    #Locale
    tornado.options.define('default_locale', default='en', type=str,
        help='Default locale setting')

    #Disqus
    tornado.options.define('disqus_enabled', default=False, type=bool,
        help='Disqus widget enabled')
    tornado.options.define('disqus_shortname', type=str,
        help='Disqus short name')

    if os.path.exists(path):
        tornado.options.parse_config_file(path)
    else:
        raise ValueError('No config file at %s' % path)

    tornado.options.parse_command_line()

    if not tornado.options.options.cookie_secret:
        tornado.options.options.cookie_secret = base64.b64encode(os.urandom(32))
    return tornado.options.options
