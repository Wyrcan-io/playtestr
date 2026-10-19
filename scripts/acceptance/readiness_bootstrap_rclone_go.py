"""Use a separate owned official SDK for Rclone's Go >=1.26 requirement."""
import readiness_bootstrap_go as bootstrap
from readiness_evidence import RAW


if __name__ == '__main__':
    bootstrap.RAW = RAW / 'active/rclone'
    bootstrap.VERSION = 'go1.27.0'
    bootstrap.main()
