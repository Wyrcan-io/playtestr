# mg scenario catalog draft v1

Status: draft only. The pinned source has been acquired and independently hashed;
native Linux/macOS source builds and the N01 first-use pilot have passed. Freeze
public cases only after each case has a reviewed, observable screen/state oracle
and its key route has been checked against the pinned mg source.

All cases use disposable synthetic files, an owned CWD/HOME/temp tree, `mg -S -n`,
and exact saved-byte assertions. `-S` avoids startup files and editor-launched
programs; `-n` disables backups. Each pass must also assert a useful terminal
checkpoint and exact exit/cleanup. Cases never touch a real user file.

## Eight normal workflows

| ID | Workflow | Intended oracle |
| --- | --- | --- |
| N01 | Create a new file, type text, `C-x C-s`, quit | Exact new file bytes; saved buffer exits without a dirty-buffer prompt |
| N02 | Open a fixture, append a line, save | Original prefix plus exact appended text and newline bytes |
| N03 | Search for a unique word, replace it through the public key route | Only the intended occurrence changes in the saved file |
| N04 | Mark a region, cut, move, and yank | Exact reordered text and visible region/edit checkpoint |
| N05 | Delete a suffix, undo, consume the modified marker, redo | Screen and final bytes agree with the reviewed text state |
| N06 | Use `C-x C-w` to save as a second filename | Original file unchanged; new path has exact expected bytes |
| N07 | Open a second file and switch back to the first buffer | Correct filename/buffer on screen; independent exact state for both files |
| N08 | Edit UTF-8 text including a wide character and save | Exact UTF-8 bytes; terminal displays the intended text without replacement glyphs |

## Twelve edge workflows

| ID | Edge | Intended oracle |
| --- | --- | --- |
| E01 | Start from a zero-byte file and save without edits | File remains zero bytes; clean exit |
| E02 | Move forward at EOF and back at BOF | Bounded refusal/beep, cursor stays at the documented boundary, bytes unchanged |
| E03 | Delete backward at the beginning of a line | The exact previous-line/newline behavior observed from baseline |
| E04 | Edit a line longer than the viewport and save | Full bytes preserved; redraw and horizontal visibility remain bounded |
| E05 | Move/delete around a multibyte wide character | No split UTF-8 sequence; exact expected bytes and screen width |
| E06 | Toggle read-only buffer mode and attempt an edit/save | Visible read-only failure, fixture bytes unchanged |
| E07 | Save-as into a missing parent directory | Clear error/refusal, no outside path or partial artifact |
| E08 | Save-as to a filename containing spaces | Exact new path and bytes; no shell interpretation |
| E09 | Cancel a filename prompt with `C-g` | Current buffer and all file states remain unchanged |
| E10 | Overwrite a pre-existing save-as destination | Observe the actual confirmation; test both decline and accept in separate variants |
| E11 | Resize while editing, then continue and save | Screen returns to a useful checkpoint and file bytes are exact |
| E12 | Attempt quit with unsaved edits, decline discard, then save and quit | First refusal preserves the editor; later save produces exact bytes and clean exit |

## Fault feasibility (not yet credited)

1. In the save path (`src/file.c`/`src/fileio.c`), use a minimal mutation that
   reports success without writing. A baseline save scenario must detect the
   unchanged/missing file, then restoration must reproduce the reviewed source
   tree exactly.
2. In the line deletion path (`src/line.c`), perturb one byte at a boundary so
   the observed saved file differs. Use only a synthetic fixture and restore
   exact source bytes before the next mutation.
3. In undo (`src/undo.c`), make one undo action fail to restore the prior buffer.
   The screen and exact file oracle must identify the false result. Restore and
   reverify source hashes.

No fault is frozen until a source review identifies the exact line and the native
baseline/fault/restoration run demonstrates one reproducible externally visible
failure per mutation. Faults that do not produce a reliable oracle are replaced,
not weakened.

E06 uses mg's explicit read-only buffer command because Playtestr intentionally
normalizes fixture file permissions to writable when preparing a managed
workspace. This exercises mg's buffer read-only guard without claiming a
read-only filesystem fixture.
