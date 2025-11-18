import logging
import os

from pyftpdlib.handlers import FTPHandler

logger = logging.getLogger(__name__)

class ScannerHandler(FTPHandler):
    """
    Custom FTP handler for processing uploaded PDF files.

    This class extends the `pyftpdlib.handlers.FTPHandler` to add functionality
    for handling uploaded files. Specifically, it enqueues PDF files to a
    ProcessingManager for asynchronous processing with retries and idempotency.
    """

    processor = None
    manager = None

    def on_file_received(self, file_path):
        """
        Called when a file upload is completed.

        This method is triggered after a file is successfully uploaded to the FTP server.
        It checks if the file is a PDF and enqueues it to the ProcessingManager for
        asynchronous processing. Falls back to synchronous processing if manager is not set.

        Args:
            file_path (str): The path to the uploaded file.
        """
        logger.info(f"File received: {file_path}")

        if not file_path.lower().endswith('.pdf'):
            logger.warning(f"Skipping non-PDF file: {file_path}")
            return

        if self.manager:
            try:
                self.manager.submit_file(file_path)
                logger.info("File enqueued for asynchronous processing: %s", file_path)
            except Exception as e:
                logger.error("Error enqueuing file for processing: %s", e)
        else:
            # Fallback to old behavior if manager not present
            logger.warning("Processing manager not configured, attempting synchronous processing")
            try:
                if self.processor:
                    success = self.processor.process_document(file_path)

                    if success:
                        try:
                            os.remove(file_path)
                            logger.info(f"Deleted processed file: {file_path}")
                        except Exception as e:
                            logger.error(f"Error deleting file: {e}")
                    else:
                        logger.error(f"Failed to process document: {file_path}")
                else:
                    logger.error("Document processor not initialized")

            except Exception as e:
                logger.error(f"Error in file received handler: {e}")
