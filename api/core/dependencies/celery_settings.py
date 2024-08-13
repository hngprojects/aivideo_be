from kombu import Queue, Exchange
# Sentry

# By default CELERYD_HIJACK_ROOT_LOGGER = True
# Is important variable that allows Celery to overlap other custom logging handlers
CELERYD_HIJACK_ROOT_LOGGER = False

# LOGGING = {
#     'handlers': {
#         'celery_sentry_handler': {
#             'level': 'ERROR',
#             'class': 'core.log.handlers.CelerySentryHandler'
#         }
#     },

#     'loggers': {
#         'celery': {
#             'handlers': ['celery_sentry_handler'],
#             'level': 'ERROR',
#             'propagate': False,
#         },
#     }
# }

# ...
#
# Prioritize your tasks! 
#

CELERY_QUEUES = (
    Queue('high', Exchange('high'), routing_key='high'),
    Queue('normal', Exchange('normal'), routing_key='normal'),
    Queue('low', Exchange('low'), routing_key='low'),
)

CELERY_DEFAULT_QUEUE = 'normal'
CELERY_DEFAULT_EXCHANGE = 'normal'
CELERY_DEFAULT_ROUTING_KEY = 'normal'

CELERY_ROUTES = {
    # -- HIGH PRIORITY QUEUE -- #
    'myapp.tasks.check_payment_status': {'queue': 'high'},
    # -- LOW PRIORITY QUEUE -- #
    'myapp.tasks.close_session': {'queue': 'low'},
}

# Keep result only if you really need them: CELERY_IGNORE_RESULT = False
# In all other cases it is better to have place somewhere in db
CELERY_IGNORE_RESULT = True

# ...