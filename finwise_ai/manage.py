#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    # Set the Django settings module explicitly
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finwise.settings')
    
    # Add the parent directory to sys.path to ensure imports work correctly
    current_path = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_path)
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
