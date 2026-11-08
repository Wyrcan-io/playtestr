package main

import (
	"crypto/ed25519"
	"crypto/rand"
	"os"
	"path/filepath"
	"testing"
)

func TestVerifyPackageAcceptsExactMessageAndRejectsTampering(t *testing.T) {
	publicKey, privateKey, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	message := []byte("pinned archive bytes")
	signature := ed25519.Sign(privateKey, message)
	path := filepath.Join(t.TempDir(), "package.tbz2")
	if err := os.WriteFile(path, message, 0600); err != nil {
		t.Fatal(err)
	}
	if err := verifyPackage(publicKey, signature, path); err != nil {
		t.Fatalf("valid package signature rejected: %v", err)
	}
	if err := os.WriteFile(path, []byte("tampered archive"), 0600); err != nil {
		t.Fatal(err)
	}
	if err := verifyPackage(publicKey, signature, path); err == nil {
		t.Fatal("tampered package accepted")
	}
}

func TestVerifyPackageRejectsUnboundedAndInvalidKeys(t *testing.T) {
	path := filepath.Join(t.TempDir(), "empty")
	if err := os.WriteFile(path, nil, 0600); err != nil {
		t.Fatal(err)
	}
	if err := verifyPackage(make([]byte, ed25519.PublicKeySize), make([]byte, ed25519.SignatureSize), path); err == nil {
		t.Fatal("empty signed package accepted")
	}
	if err := verifyPackage(nil, nil, path); err == nil {
		t.Fatal("malformed key and signature accepted")
	}
}
