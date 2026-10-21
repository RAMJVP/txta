import json, logging, sys

def configure_logging():
    handler=logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(message)s'))
    root=logging.getLogger(); root.handlers=[handler]; root.setLevel(logging.INFO)

def log_event(logger, event, **fields):
    safe={'event':event, **fields}
    logger.info(json.dumps(safe, default=str, separators=(',',':')))
