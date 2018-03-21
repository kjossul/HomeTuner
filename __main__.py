import threading
from HomeTuner import setup_logging, scan, init_assets, create_app

setup_logging()
init_assets()
scanner = threading.Thread(target=scan.main, args=[])
scanner.start()
app = create_app()
app.run(host='0.0.0.0', threaded=True)