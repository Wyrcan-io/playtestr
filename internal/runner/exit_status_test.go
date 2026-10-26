package runner

import (
	"fmt"
	"strconv"
	"testing"
)

func TestExitStatusBoundsBySpecVersion(t *testing.T) {
	for _, version := range []int{1, 2, 3} {
		for _, code := range []string{"-1", "0", "255", "256", "3221225786", "4294967295", "4294967296", "1.5"} {
			t.Run(fmt.Sprintf("v%d/%s", version, code), func(t *testing.T) {
				workspace := ""
				if version >= 2 {
					workspace = `,"workspace":{"fixture":"fixture"}`
				}
				data := fmt.Sprintf(`{"version":%d,"command":["trusted-target"]%s,"steps":[{"exit":%s}]}`, version, workspace, code)
				_, err := decodeSpec([]byte(data), "native-status.json")
				valid := code == "0" || code == "255" || version == 3 && (code == "256" || strconv.IntSize == 64 && (code == "3221225786" || code == "4294967295"))
				if (err == nil) != valid {
					t.Fatalf("exit %s for v%d: valid=%v, error=%v", code, version, valid, err)
				}
			})
		}
	}
}
