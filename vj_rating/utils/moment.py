from datetime import datetime
from distutils.version import StrictVersion

import pytz
from flask import current_app
from flask_moment import _moment
from jinja2 import Markup

CHINA_STANDART_TIME_ZONE = pytz.timezone('Asia/Shanghai')


class hooked_moment(_moment):
    @staticmethod
    def include_moment(version='2.18.1', local_js=None, no_js=None):
        js = ''
        if not no_js:
            if local_js is not None:
                js = '<script src="%s"></script>\n' % local_js
            elif version is not None:
                js_filename = 'moment-with-locales.min.js' \
                    if StrictVersion(version) >= StrictVersion('2.8.0') \
                    else 'moment-with-langs.min.js'
                js = '<script src="//cdn.bootcss.com/moment.js/%s/%s"></script>\n' % (
                    version, js_filename)
        return Markup('''%s<script>
moment.locale("en");
function flask_moment_render(elem) {
    if ($(elem).data('is-duration') === undefined){
        $(elem).text(eval('moment("' + $(elem).data('timestamp') + '").' + $(elem).data('format') + ';'));
    }else{
        cmd = `moment.duration(moment('${$(elem).data('timestamp')}').diff('${$(elem).data('from')}')).${$(elem).data('format')};`
        $(elem).text(eval(cmd));
    }
    $(elem).removeClass('flask-moment').show();
}
function flask_moment_render_all() {
    $('.flask-moment').each(function() {
        flask_moment_render(this);
        if ($(this).data('refresh')) {
            (function(elem, interval) { setInterval(function() { flask_moment_render(elem) }, interval); })(this, $(this).data('refresh'));
        }
    })
}
$(document).ready(function() {
    flask_moment_render_all();
});
</script>''' % js)

    def duration_from(self, from_timestamp, _format='HH:mm:ss'):
        t = self._timestamp_as_iso_8601(self.timestamp)
        template = '''
        <span class="flask-moment" data-is-duration="{}" data-timestamp="{}"
                       data-format="format('{}')" data-from={} data-refresh="{}"
                       style="display: none">{}</span>
        '''.format(1, t, _format, self._timestamp_as_iso_8601(from_timestamp), 0, t)
        return Markup(template)

    @staticmethod
    def current_year():
        return str(datetime.today().year)


class Moment(object):
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['moment'] = hooked_moment
        app.context_processor(self.context_processor)

    @staticmethod
    def context_processor():
        return {
            'moment': current_app.extensions['moment']
        }

    def create(self, timestamp=None):
        return current_app.extensions['moment'](timestamp)
