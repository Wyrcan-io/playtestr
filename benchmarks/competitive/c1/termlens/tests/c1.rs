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

#[test]
fn c2_stateful_setup() -> termlens::Result<()> {
    let binary = env::var("C2_STATEFUL_BIN").expect("C2_STATEFUL_BIN must name the target");
    let config = PathBuf::from(env::var("C2_CONFIG_PATH").expect("C2_CONFIG_PATH is required"));
    let mut terminal = Terminal::builder()
        .size(60, 12)
        .env_clear()
        .env("C2_CONFIG_PATH", &config)
        .timeout(Duration::from_secs(5))
        .spawn(binary)?;

    terminal.wait_until(|screen| screen.contains("Port (1024-65535):"))?;
    terminal.send_str("invalid")?;
    terminal.send(Key::Enter)?;
    terminal.wait_until(|screen| screen.contains("Invalid port"))?;
    terminal.send_str("4242")?;
    terminal.send(Key::Enter)?;
    terminal.wait_until(|screen| screen.contains("Saved port 4242"))?;
    assert!(terminal.wait_exit()?.success());
    assert_eq!(fs::read_to_string(config).expect("read config oracle"), "port=4242\n");
    Ok(())
}

#[test]
fn c3_resize_redraw() -> termlens::Result<()> {
    let binary = env::var("C3_RESIZE_BIN").expect("C3_RESIZE_BIN must name the target");
    let mut terminal = Terminal::builder()
        .size(60, 12)
        .env_clear()
        .timeout(Duration::from_secs(5))
        .spawn(binary)?;

    terminal.wait_until(|screen| screen.contains("Main screen"))?;
    terminal.send_str("?")?;
    terminal.wait_until(|screen| screen.contains("Help modal"))?;
    terminal.resize(80, 20)?;
    terminal.wait_until(|screen| screen.contains("Size: 80x20"))?;
    terminal.send(Key::Esc)?;
    terminal.wait_until(|screen| {
        screen.contains("Press ? for help") && !screen.contains("Help modal")
    })?;
    terminal.send_str("q")?;
    assert!(terminal.wait_exit()?.success());
    Ok(())
}
