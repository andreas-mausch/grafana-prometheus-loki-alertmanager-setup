import logging
import sys

format = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format=format)

logging.info("My Service")
logging.info("==========")
logging.info("")
logging.info("Enter 1 to produce a warning")
logging.info("Enter 2 to throw")
logging.info("Enter free text to echo it to the log")

running = True

while running:
  try:
    text = input()
    if text == "1":
      logging.warning("A warning occured!")
    elif text == "2":
      raise Exception("An error occured!")
    else:
      logging.info(text)
  except Exception as e:
    logging.exception(e)
  except KeyboardInterrupt:
    logging.info("Exiting")
    running = False
