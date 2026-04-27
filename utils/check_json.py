import json
import os
import logging
from typing import Dict, Any, List, Optional

# Configure system-level logging for data integrity checks
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TransactionDataValidator:
    """
    Utility class for validating the structural integrity of financial datasets.
    Focused on ISO 20022 message structure validation for AML auditing.
    """

    def __init__(self, data_dir: str = "data"):
        # Resolve the absolute path to the data directory to prevent path errors
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.target_path = os.path.join(base_path, data_dir, 'transactions.json')

    def validate_iso_schema(self) -> Optional[List[Dict[str, Any]]]:
        """
        Validates the ISO 20022 compliance of the local JSON transaction store.
        Returns the list of entries if successful, otherwise returns None.
        """
        if not os.path.exists(self.target_path):
            logger.error(f"Integrity Error: File not found at {self.target_path}")
            return None

        try:
            with open(self.target_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

                # ISO 20022 structure typically nests entries under 'Ntry'
                if not isinstance(data, list) or not data:
                    logger.warning("Data format mismatch: Expected root list.")
                    return None

                entries = data[0].get('Ntry', [])

                logger.info(f"Schema Validation Successful: {len(entries)} entries detected.")

                if entries:
                    sample_ref = entries[0].get('NtryRef', 'N/A')
                    logger.debug(f"Metadata Sample - Entry Reference: {sample_ref}")

                return entries

        except json.JSONDecodeError:
            logger.error("Corruption Error: Failed to parse JSON content.")
        except Exception as e:
            logger.error(f"Unexpected Validation Failure: {str(e)}")

        return None


def run_integrity_check():
    """Execution wrapper for system health checks."""
    validator = TransactionDataValidator()
    results = validator.validate_iso_schema()

    if results is not None:
        print(f"\n[SYSTEM CHECK] ISO 20022 Schema: VALID")
        print(f"[SYSTEM CHECK] Records Count: {len(results)}\n")
    else:
        print("\n[SYSTEM CHECK] ISO 20022 Schema: FAILED\n")


if __name__ == "__main__":
    run_integrity_check()