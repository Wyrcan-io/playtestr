package console

import (
	"fmt"
	"strings"
	"unicode/utf8"
)

// Event represents exactly one supported input action.
type Event struct{ Key, Text string }

var sequences = map[string]string{
	"\x1b[A": "ArrowUp", "\x1b[B": "ArrowDown", "\x1b[C": "ArrowRight", "\x1b[D": "ArrowLeft",
	"\x1b[1~": "Home", "\x1b[H": "Home", "\x1bOH": "Home", "\x1b[7~": "Home",
	"\x1b[4~": "End", "\x1b[F": "End", "\x1bOF": "End", "\x1b[8~": "End",
	"\x1b[5~": "PageUp", "\x1b[6~": "PageDown",
	"\r": "Enter", "\n": "Enter", "\t": "Tab", "\x7f": "Backspace", "\b": "Backspace",
	"\x03": "CtrlC", "\x05": "CtrlE", "\x0f": "CtrlO", "\x00": "CtrlSpace", "\x06": "CtrlF", "\x11": "CtrlQ", "\x13": "CtrlS", "\x1a": "CtrlZ",
}

// Decode never silently drops unsupported sequences. Incomplete UTF-8/escapes
// remain buffered; flush disambiguates a lone Escape after an idle interval.
func Decode(buffer []byte, flush bool) ([]Event, []byte, error) {
	var events []Event
	for len(buffer) > 0 {
		if buffer[0] == 27 {
			matched := false
			for seq, key := range sequences {
				if len(seq) > 1 && strings.HasPrefix(string(buffer), seq) {
					events = append(events, Event{Key: key})
					buffer = buffer[len(seq):]
					matched = true
					break
				}
			}
			if matched {
				continue
			}
			if len(buffer) == 1 {
				if !flush {
					return events, buffer, nil
				}
				events = append(events, Event{Key: "Escape"})
				buffer = buffer[1:]
				continue
			}
			for seq := range sequences {
				if strings.HasPrefix(seq, string(buffer)) && !flush {
					return events, buffer, nil
				}
			}
			return events, nil, fmt.Errorf("unsupported escape sequence; use /key or /text in the control console")
		}
		if key, ok := sequences[string(buffer[:1])]; ok {
			events = append(events, Event{Key: key})
			buffer = buffer[1:]
			continue
		}
		if !utf8.FullRune(buffer) {
			if !flush {
				return events, buffer, nil
			}
			return events, nil, fmt.Errorf("incomplete UTF-8 input")
		}
		r, size := utf8.DecodeRune(buffer)
		if r == utf8.RuneError && size == 1 {
			return events, nil, fmt.Errorf("invalid UTF-8 input")
		}
		if r < 32 {
			return events, nil, fmt.Errorf("unsupported control input U+%04X; use explicit /text if intentional", r)
		}
		events = append(events, Event{Text: string(buffer[:size])})
		buffer = buffer[size:]
	}
	return events, nil, nil
}
