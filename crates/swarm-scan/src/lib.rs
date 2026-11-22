//! Performance-critical primitives for swamAi.
//!
//! This crate is where CPU- or IO-bound work moves off the Python core:
//! concurrent host sweeps, packet/log parsing, scoring over large graphs.
//! It's a stub today — one honest function plus the PyO3 wiring commented out
//! so the first real hot path has a clear home.

/// Expand a simple CIDR-ish `base`/`count` into host strings.
/// Placeholder for a real concurrent sweep built on this crate.
pub fn host_range(base: &str, count: u8) -> Vec<String> {
    (0..count).map(|i| format!("{base}{i}")).collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn expands_hosts() {
        assert_eq!(host_range("10.0.0.", 3), ["10.0.0.0", "10.0.0.1", "10.0.0.2"]);
    }
}

// --- Python binding (enable with the `pyo3` dependency + maturin) ---
// use pyo3::prelude::*;
//
// #[pyfunction]
// fn host_range_py(base: &str, count: u8) -> Vec<String> { host_range(base, count) }
//
// #[pymodule]
// fn swarm_scan(m: &Bound<'_, PyModule>) -> PyResult<()> {
//     m.add_function(wrap_pyfunction!(host_range_py, m)?)?;
//     Ok(())
// }
