#!/usr/bin/env python3
"""
Echo Pipeline - Эталонный пайплайн для тестирования
"""

import time
from ..core.base import BasePipeline, Request, Response

class Echo(BasePipeline):
    """Эталонный echo пайплайн"""
    
    def __init__(self):
        super().__init__("Echo")
        
    def execute(self, request: Request) -> Response:
        """Эхо-ответ для тестирования"""
        start_time = time.time()
        
        # Имитируем минимальную задержку
        time.sleep(0.001)
        
        latency = time.time() - start_time
        
        # Возвращаем эхо-ответ
        echo_data = f"Echo from {request.host}:{request.port}".encode()
        
        return Response(
            success=True,
            status_code=200,
            data=echo_data,
            latency=latency
        )
