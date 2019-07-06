import logging
import sys


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    handlers= [logging.StreamHandler(sys.stdout),
                               logging.FileHandler('bot_log'),
                               ],
                    )
logger = logging.getLogger(__name__)
