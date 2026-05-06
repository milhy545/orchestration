"""Unit tests for mega_orchestrator.utils.hw_detect."""

from __future__ import annotations

import importlib
import sys
from unittest import mock

import pytest

hw_detect = importlib.import_module("mega_orchestrator.utils.hw_detect")


class TestDetectHardware:
    def test_returns_required_keys(self):
        result = hw_detect.detect_hardware()
        for key in ("hostname", "os", "cpu", "cpu_cores", "ram_gb", "gpu", "ip"):
            assert key in result, f"Missing key: {key}"

    def test_cpu_cores_non_negative(self):
        result = hw_detect.detect_hardware()
        assert result["cpu_cores"] >= 0

    def test_ram_gb_non_negative(self):
        result = hw_detect.detect_hardware()
        assert result["ram_gb"] >= 0.0

    def test_cpu_is_string(self):
        result = hw_detect.detect_hardware()
        assert isinstance(result["cpu"], str)
        assert result["cpu"]  # non-empty

    def test_gpu_is_string(self):
        result = hw_detect.detect_hardware()
        assert isinstance(result["gpu"], str)

    def test_ip_is_string(self):
        result = hw_detect.detect_hardware()
        assert isinstance(result["ip"], str)


class TestDetectCpu:
    def test_reads_proc_cpuinfo(self, tmp_path):
        fake_cpuinfo = tmp_path / "cpuinfo"
        fake_cpuinfo.write_text(
            "processor\t: 0\nmodel name\t: Intel(R) Core(TM) i5-4690K @ 3.50GHz\n"
        )
        result = hw_detect._detect_cpu(cpuinfo_path=str(fake_cpuinfo))
        assert "i5-4690K" in result

    def test_fallback_on_oserror(self, tmp_path):
        result = hw_detect._detect_cpu(cpuinfo_path=str(tmp_path / "nonexistent"))
        assert isinstance(result, str)


class TestDetectRamGb:
    def test_parses_meminfo(self, tmp_path):
        fake = tmp_path / "meminfo"
        fake.write_text("MemTotal:       32768000 kB\nMemFree: 10000000 kB\n")
        result = hw_detect._detect_ram_gb(meminfo_path=str(fake))
        # 32768000 kB / 1_048_576 = 31.25; round(31.25, 1) = 31.2 (Python banker's rounding)
        assert result == pytest.approx(31.2, abs=0.05)

    def test_returns_zero_on_error(self, tmp_path):
        result = hw_detect._detect_ram_gb(meminfo_path=str(tmp_path / "nonexistent"))
        assert result == 0.0


class TestDetectGpu:
    def test_prefers_nvidia_smi(self):
        with mock.patch(
            "subprocess.check_output", return_value=b"NVIDIA GeForce GTX 1060\n"
        ):
            result = hw_detect._detect_gpu()
        assert "GTX 1060" in result

    def test_falls_back_to_lspci(self):
        def side_effect(cmd, **kwargs):
            if "nvidia-smi" in cmd:
                raise FileNotFoundError
            return b"00:02.0 VGA compatible controller: Intel HD Graphics 4600\n"

        with mock.patch("subprocess.check_output", side_effect=side_effect):
            result = hw_detect._detect_gpu()
        assert "HD Graphics" in result or "Intel" in result

    def test_returns_unknown_when_all_fail(self):
        with mock.patch("subprocess.check_output", side_effect=Exception("nope")):
            result = hw_detect._detect_gpu()
        assert result == "unknown"


class TestDetectIp:
    def test_returns_string(self):
        result = hw_detect._detect_ip()
        assert isinstance(result, str)

    def test_fallback_on_socket_error(self):
        with mock.patch("socket.socket") as mock_sock:
            mock_sock.return_value.__enter__.return_value.connect.side_effect = OSError
            result = hw_detect._detect_ip()
        assert result == "unknown"
