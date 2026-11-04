"""Install the pinned official Go SDK under the active next-twenty Skim root."""
from next20_check import RAW
from readiness_bootstrap_go import main as install_go


def main():
    install_go(owned=RAW / 'active' / 'skim' / 'go-toolchain')


if __name__ == '__main__':
    main()
