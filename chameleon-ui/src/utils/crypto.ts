// src/utils/crypto.ts

import { sm2 } from 'sm-crypto-v2';

// 从后端获取或配置公钥
const SM2_PUBLIC_KEY: string = "04535ae65ad7809a9600fa58ca27cda8785dfb964f566d61365d64f3b4307208a42cf5202aa0e7f163216c69f37f0e71287d573d88351bc794dba78d5e6abc2bd8"; // 替换为实际公钥

export function getPublicKey(): string {
    return SM2_PUBLIC_KEY;
}

export function encryptData(plaintext: string, publicKey: string): string | null {
    if (!plaintext || !publicKey) {
        console.error("Missing plaintext or publicKey for encryption");
        return null;
    }
    try {
        // sm2 已经正确导入
        const cipherMode = 1; // C1C3C2 mode
        // sm2.doEncrypt 返回 hex string
        return sm2.doEncrypt(plaintext, publicKey, cipherMode);
    } catch (err) {
        console.error("Encryption error:", err);
        return null;
    }
}

export function decryptData(ciphertextHex: string, privateKey: string): string | null {
    if (!ciphertextHex || !privateKey) {
        console.error("Missing ciphertext or privateKey for decryption");
        return null;
    }
    try {
        // 确保 ciphertextHex 是一个有效的十六进制字符串
        const hexRegex = /^[0-9a-fA-F]+$/;
        if (!hexRegex.test(ciphertextHex)) {
            console.error("Ciphertext is not a valid hex string");
            return null;
        }
        const cipherMode = 1;
        // sm2.doDecrypt 需要 hex string 作为输入
        return sm2.doDecrypt(ciphertextHex, privateKey, cipherMode);
    } catch (err) {
        console.error("Decryption error:", err);
        // 可以根据需要返回更具体的错误信息或 null
        return null;
    }
}