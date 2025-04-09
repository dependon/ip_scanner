import pytest
from ip_scanner import IPScanner

@pytest.fixture
def ip_scanner():
    return IPScanner()

def test_scan_single_ip(ip_scanner):
    # 测试单个IP扫描
    result = ip_scanner.scan_ip('127.0.0.1')
    assert isinstance(result, bool)

def test_scan_range(ip_scanner):
    # 测试IP范围扫描
    ip_scanner.scan_range(1, 2)  # 只扫描两个IP以加快测试速度
    assert True  # 如果没有异常就通过

def test_load_config(ip_scanner):
    # 测试配置加载
    language = ip_scanner.load_config()
    assert language is None or isinstance(language, str)

def test_invalid_ip_range(ip_scanner):
    # 测试无效的IP范围
    with pytest.raises(ValueError):
        ip_scanner.scan_range(256, 1)  # 无效的范围

def test_invalid_ip_format(ip_scanner):
    # 测试无效的IP格式
    with pytest.raises(ValueError):
        ip_scanner.scan_ip('invalid.ip.address')