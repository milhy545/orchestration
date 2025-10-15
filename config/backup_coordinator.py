#!/usr/bin/env python3
import sys
import os
sys.path.append('/home/orchestration/mega_orchestrator')
from backup_coordinator import main
import asyncio

if __name__ == '__main__':
    asyncio.run(main())
