use std::{env, fs, path::PathBuf, time::Duration};

use termlens::{Key, Terminal};

#[test]
fn c1_selection() -> termlens::Result<()> {
    let binary = env::var("C1_SELECTOR_BIN").expect("C1_SELECTOR_BIN must name the target");
    let result = PathBuf::from(env::var("C1_RESULT_PATH").expect("C1_RESULT_PATH is required"));
    let mut terminal = Terminal::builder()
        .size(60, 12)
        .env_clear()
        .env("C1_RESULT_PATH", &result)
        .timeout(Duration::from_secs(5))
        .spawn(binary)?;

    terminal.wait_until(|screen| screen.contains("Select record"))?;
    terminal.send(Key::Down)?;
    terminal.wait_until(|screen| screen.contains("> Beta"))?;
    terminal.send(Key::Enter)?;
    terminal.wait_until(|screen| screen.contains("Selected: Beta"))?;
    assert!(terminal.wait_exit()?.success());
    assert_eq!(fs::read_to_string(result).expect("read target oracle"), "Beta\n");
    Ok(())
}
