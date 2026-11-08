package main

import (
	"crypto/ed25519"
	"encoding/base64"
	"errors"
	"fmt"
	"os"
)

const maxPackageBytes = 128 * 1024 * 1024

func verifyPackage(publicKey, signature []byte, packagePath string) error {
	if len(publicKey) != ed25519.PublicKeySize {
		return fmt.Errorf("invalid Ed25519 public key length: %d", len(publicKey))
	}
	if len(signature) != ed25519.SignatureSize {
		return fmt.Errorf("invalid Ed25519 signature length: %d", len(signature))
	}
	info, err := os.Stat(packagePath)
	if err != nil {
		return fmt.Errorf("stat signed package: %w", err)
	}
	if !info.Mode().IsRegular() || info.Size() <= 0 || info.Size() > maxPackageBytes {
		return errors.New("signed package is not a bounded regular file")
	}
	message, err := os.ReadFile(packagePath)
	if err != nil {
		return fmt.Errorf("read signed package: %w", err)
	}
	if !ed25519.Verify(ed25519.PublicKey(publicKey), message, signature) {
		return errors.New("MacPorts package Ed25519 signature failed")
	}
	return nil
}

func main() {
	if len(os.Args) != 4 {
		fmt.Fprintln(os.Stderr, "usage: verifier BASE64_PUBLIC_KEY BASE64_SIGNATURE PACKAGE")
		os.Exit(2)
	}
	publicKey, err := base64.StdEncoding.DecodeString(os.Args[1])
	if err != nil {
		fmt.Fprintln(os.Stderr, "decode public key:", err)
		os.Exit(2)
	}
	signature, err := base64.StdEncoding.DecodeString(os.Args[2])
	if err != nil {
		fmt.Fprintln(os.Stderr, "decode signature:", err)
		os.Exit(2)
	}
	if err := verifyPackage(publicKey, signature, os.Args[3]); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
