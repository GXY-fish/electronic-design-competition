# 导入加密模块 ucryptolib
# (Import the ucryptolib encryption module)
import ucryptolib

def test_aes():
    # 打印测试 AES 加密/解密的信息
    # (Print information about testing AES encryption/decryption)
    print("Testing AES encryption/decryption...")

    # 定义 AES-128 ECB 模式的测试
    # (Define the test for AES-128 ECB mode)
    key = b'1234567890abcdef'  # 16 字节的密钥
    # (16-byte key)
    plaintext = b'This is 16 bytes'  # 16 字节的明文
    # (16-byte plaintext)
    print("\nTest 1: AES-128 ECB")
    
    # 创建 AES-128 ECB 模式的加密实例
    # (Create an AES-128 ECB mode encryption instance)
    cipher = ucryptolib.aes(key, ucryptolib.MODE_ECB)
    encrypted = cipher.encrypt(plaintext)
    
    # 创建新的 AES-128 ECB 模式的解密实例
    # (Create a new AES-128 ECB mode decryption instance)
    cipher = ucryptolib.aes(key, ucryptolib.MODE_ECB)
    decrypted = cipher.decrypt(encrypted)
    
    # 断言解密后的明文与原始明文相同
    # (Assert that the decrypted plaintext is the same as the original plaintext)
    assert decrypted == plaintext, "AES-128 ECB failed"
    print("Passed")

    # 测试密钥长度不合法的情况
    # (Test the case of an invalid key length)
    print("\nTest 2: Invalid key length")
    try:
        # 尝试使用短密钥创建 AES 实例，应该引发 ValueError 异常
        # (Try to create an AES instance with a short key, which should raise a ValueError)
        ucryptolib.aes(b'short_key', ucryptolib.MODE_ECB)
        assert False, "Invalid key not detected"
    except ValueError:
        print("Passed")

    # 测试数据长度不对齐的情况
    # (Test the case of unaligned data length)
    print("\nTest 3: Unaligned data length")
    cipher = ucryptolib.aes(key, ucryptolib.MODE_ECB)
    try:
        # 尝试加密长度不是 16 字节的数据，应该引发 ValueError 异常
        # (Try to encrypt data with a length that is not 16 bytes, which should raise a ValueError)
        cipher.encrypt(b'short')
        assert False, "Unaligned data not detected"
    except ValueError:
        print("Passed")

    # 打印所有 AES 测试都通过的信息
    # (Print the information that all AES tests passed successfully)
    print("\nAll AES tests passed successfully!")

# 执行 AES 测试函数
# (Execute the AES test function)
test_aes()