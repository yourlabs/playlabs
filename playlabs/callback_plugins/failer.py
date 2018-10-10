import sys

from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):
    """
    This callback module exists non-zero if no hosts match
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'failer'
    CALLBACK_NEEDS_WHITELIST = False

    def __init__(self):
        super(CallbackModule, self).__init__()

    def v2_runner_on_unreachable(self, result):
        sys.exit(1)

    def v2_playbook_on_no_hosts_matched(self):
        sys.exit(1)

    def v2_playbook_on_stats(self, stats):
        found_stats = False

        for key in ['ok', 'failures', 'dark', 'changed', 'skipped']:
            if len(getattr(stats, key)) > 0:
                found_stats = True
                break

        if not found_stats:
            sys.exit(1)
