import click


def _load_session():
    return {
        'transfer': {
            'endpoint_id': 'ddb59aef-6d04-11e5-ba46-22000b92c6ec'
        }
    }


class SessionLoadedOption(click.Option):
    """
    Customized Option type to load values from config. Might still be required.
    """
    def __init__(self, *args, **kwargs):
        session_key = kwargs.pop('session_key').split('.')
        value = _load_session()
        for k in session_key:
            if value is None:
                break
            value = value.get(k)
        self.session_value = value

        super(SessionLoadedOption, self).__init__(*args, **kwargs)

    def value_is_missing(self, value):
        if self.session_value is not None:
            return False
        else:
            return super(SessionLoadedOption, self).value_is_missing(value)

    def process_value(self, ctx, value):
        v = value if self.session_value is None else self.session_value
        return super(SessionLoadedOption, self).process_value(ctx, v)
