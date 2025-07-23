from ttkthemes import ThemedTk
import logging
import traceback
from gui import VISA4DGui

def main():
    try:
        # Configure logging
        logging.basicConfig(
            filename='visa4d.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Initialize GUI
        root = ThemedTk(theme="arc")
        app = VISA4DGui(root)
        root.mainloop()
        
    except Exception as e:
        logging.critical(f"Application crash: {str(e)}\n{traceback.format_exc()}")
        raise

if __name__ == "__main__":
    main()
