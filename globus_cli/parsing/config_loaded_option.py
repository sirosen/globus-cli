import click
from globus_cli.config import lookup_option


class ConfigLoadedOption(click.Option):
    """
    Customized Option type to load values from config.
    Supports required arguments that can be loaded from config.
    """
    def __init__(self, *args, **kwargs):
        section, key = kwargs.pop('config_key')
        self.session_value = lookup_option(key, section=section)

        super(ConfigLoadedOption, self).__init__(*args, **kwargs)

    def value_is_missing(self, value):
        if self.session_value is not None:
            return False
        else:
            return super(ConfigLoadedOption, self).value_is_missing(value)

    def process_value(self, ctx, value):
        v = self.session_value if value is None else value
        return super(ConfigLoadedOption, self).process_value(ctx, v)
