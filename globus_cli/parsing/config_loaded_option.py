import click
from globus_cli.config import lookup_option


class ConfigLoadedOption(click.Option):
    """
    Customized Option type to load values from config.
    Supports required arguments that can be loaded from config.
    """
    def __init__(self, *args, **kwargs):
        section, key = kwargs.pop('config_key')
        self.config_value = lookup_option(key, section=section)

        # now set default if we got a config value
        default = kwargs.pop('default', None)
        # make sure self.config_value goes *first*
        kwargs['default'] = self.config_value or default
        if kwargs['default']:
            kwargs['show_default'] = True
            kwargs['required'] = False

        super(ConfigLoadedOption, self).__init__(*args, **kwargs)

    def value_is_missing(self, value):
        if self.config_value is not None:
            return False
        else:
            return super(ConfigLoadedOption, self).value_is_missing(value)

    def process_value(self, ctx, value):
        v = self.config_value if value is None else value
        return super(ConfigLoadedOption, self).process_value(ctx, v)
