# 敏感信息脱敏规范

> 定义敏感信息的分级和脱敏处理标准

## 适用范围

本规范适用于：
- 数据库存储
- API响应
- 日志输出
- 前端展示
- 文档示例

## 1. 敏感信息分级

### 1.1 敏感级别定义

| 敏感级别 | 说明 | 处理要求 |
|---------|------|---------|
| **L3（高）** | 核心敏感信息，泄露会造成严重后果 | 存储加密 + 展示脱敏 + 日志禁止 |
| **L2（中）** | 一般敏感信息，泄露会造成一定影响 | 展示脱敏 + 日志脱敏 |
| **L1（低）** | 普通业务数据，无特殊要求 | 正常处理 |

### 1.2 敏感信息分级清单

| 信息类型 | 敏感级别 | 存储要求 | 展示要求 | 日志要求 |
|---------|---------|---------|---------|---------|
| 用户密码 | L3 | 加密存储（BCrypt/SHA256+Salt） | 严禁展示 | 严禁记录 |
| 支付密码 | L3 | 加密存储 | 严禁展示 | 严禁记录 |
| 身份证号 | L3 | 加密存储 | 脱敏展示 | 脱敏记录 |
| 银行卡号 | L3 | 加密存储 | 脱敏展示 | 脱敏记录 |
| CVV安全码 | L3 | 严禁存储 | 严禁展示 | 严禁记录 |
| 短信验证码 | L3 | 明文存储（有效期5分钟） | 严禁展示 | 严禁记录 |
| 手机号 | L2 | 明文存储 | 脱敏展示 | 脱敏记录 |
| 邮箱地址 | L2 | 明文存储 | 脱敏展示 | 可记录 |
| 真实姓名 | L2 | 明文存储 | 部分脱敏 | 可记录 |
| 家庭住址 | L2 | 明文存储 | 部分脱敏 | 脱敏记录 |
| AccessKey | L3 | 加密存储 | 严禁展示 | 严禁记录 |
| SecretKey | L3 | 加密存储 | 严禁展示 | 严禁记录 |
| 用户昵称 | L1 | 明文存储 | 正常展示 | 可记录 |
| 订单金额 | L1 | 明文存储 | 正常展示 | 可记录 |

## 2. 脱敏规则

### 2.1 手机号脱敏

**规则：** 保留前3位和后4位，中间4位用 `*` 替代

```
原始：13812345678
脱敏：138****5678
```

**实现示例（Java）：**
```java
public static String maskPhone(String phone) {
    if (phone == null || phone.length() != 11) {
        return phone;
    }
    return phone.substring(0, 3) + "****" + phone.substring(7);
}
```

### 2.2 身份证号脱敏

**规则：** 保留前6位和后4位，中间用 `*` 替代

```
原始：110101199001011234
脱敏：110101********1234
```

**实现示例（Java）：**
```java
public static String maskIdCard(String idCard) {
    if (idCard == null || idCard.length() < 10) {
        return idCard;
    }
    return idCard.substring(0, 6) + "********" + idCard.substring(idCard.length() - 4);
}
```

### 2.3 银行卡号脱敏

**规则：** 保留前4位和后4位，中间用 `*` 替代，每4位用空格分隔

```
原始：6222021234567890123
脱敏：6222 **** **** 0123
```

**实现示例（Java）：**
```java
public static String maskBankCard(String cardNo) {
    if (cardNo == null || cardNo.length() < 8) {
        return cardNo;
    }
    String first = cardNo.substring(0, 4);
    String last = cardNo.substring(cardNo.length() - 4);
    return first + " **** **** " + last;
}
```

### 2.4 邮箱地址脱敏

**规则：** 保留邮箱前缀前2位和@后的域名，中间用 `*` 替代

```
原始：zhangsan@example.com
脱敏：zh****@example.com
```

**实现示例（Java）：**
```java
public static String maskEmail(String email) {
    if (email == null || !email.contains("@")) {
        return email;
    }
    String[] parts = email.split("@");
    String prefix = parts[0];
    if (prefix.length() <= 2) {
        return email;
    }
    return prefix.substring(0, 2) + "****@" + parts[1];
}
```

### 2.5 真实姓名脱敏

**规则：** 保留姓氏，名字用 `*` 替代

```
原始：张三
脱敏：张*

原始：欧阳娜娜
脱敏：欧阳**
```

**实现示例（Java）：**
```java
public static String maskName(String name) {
    if (name == null || name.length() <= 1) {
        return name;
    }
    // 复姓处理
    if (name.length() >= 3 && isFamilyName(name.substring(0, 2))) {
        return name.substring(0, 2) + "*".repeat(name.length() - 2);
    }
    // 单姓处理
    return name.substring(0, 1) + "*".repeat(name.length() - 1);
}
```

### 2.6 家庭住址脱敏

**规则：** 保留省市区，详细地址用 `*` 替代

```
原始：北京市朝阳区建国路88号SOHO现代城A座1001室
脱敏：北京市朝阳区建国路***
```

## 3. 数据字典中的敏感级别标注

在产品PRD和研发设计文档的数据字典中，必须标注敏感级别：

| 字段标识 | 字段名称 | 类型/长度 | 必填 | 默认值 | 校验规则 | 数据来源 | **敏感级** |
|---------|---------|---------|------|-------|---------|---------|---------|
| `user_id` | 用户ID | BigInt | 是 | - | >0 | 登录态 | L3（高） |
| `phone` | 手机号 | VARCHAR(11) | 是 | - | 11位数字 | 用户输入 | L2（中） |
| `id_card` | 身份证号 | VARCHAR(18) | 是 | - | 18位 | 用户输入 | L3（高） |
| `amount` | 交易金额 | Decimal(18,2) | 是 | 0.00 | >=0.01 | 用户输入 | L1（低） |

## 4. API响应中的脱敏处理

### 4.1 响应DTO中的脱敏

**方式一：在Service层脱敏**
```java
public UserDTO getUserInfo(Long userId) {
    User user = userRepository.findById(userId);
    UserDTO dto = UserConverter.toDTO(user);

    // 脱敏处理
    dto.setPhone(SensitiveUtils.maskPhone(user.getPhone()));
    dto.setIdCard(SensitiveUtils.maskIdCard(user.getIdCard()));

    return dto;
}
```

**方式二：使用Jackson注解（推荐）**
```java
public class UserDTO {
    private Long userId;

    @JsonSerialize(using = PhoneMaskSerializer.class)
    private String phone;

    @JsonSerialize(using = IdCardMaskSerializer.class)
    private String idCard;

    private String nickname;
}
```

### 4.2 响应示例

**正确示例（已脱敏）：**
```json
{
  "code": 200,
  "msg": "查询成功",
  "data": {
    "userId": 10001,
    "phone": "138****5678",
    "idCard": "110101********1234",
    "nickname": "张三"
  }
}
```

**错误示例（未脱敏）：**
```json
{
  "code": 200,
  "msg": "查询成功",
  "data": {
    "userId": 10001,
    "phone": "13812345678",  // ❌ 未脱敏
    "idCard": "110101199001011234",  // ❌ 未脱敏
    "nickname": "张三"
  }
}
```

## 5. 日志中的脱敏处理

### 5.1 日志脱敏规则

| 场景 | 处理方式 |
|------|---------|
| L3级敏感信息 | 严禁记录到日志 |
| L2级敏感信息 | 必须脱敏后记录 |
| L1级普通信息 | 可正常记录 |

### 5.2 日志脱敏示例

**正确示例：**
```java
// 用户登录日志
log.info("用户登录成功, userId={}, phone={}", userId, SensitiveUtils.maskPhone(phone));

// 订单创建日志
log.info("创建订单成功, orderId={}, userId={}, amount={}", orderId, userId, amount);
```

**错误示例：**
```java
// ❌ 记录了完整手机号
log.info("用户登录成功, userId={}, phone={}", userId, phone);

// ❌ 记录了密码
log.info("用户登录, username={}, password={}", username, password);
```

## 6. 数据库存储加密

### 6.1 加密存储字段

以下字段必须加密存储：
- 用户密码（使用BCrypt或SHA256+Salt）
- 支付密码
- 身份证号
- 银行卡号
- AccessKey/SecretKey

### 6.2 加密方案

**密码加密（BCrypt）：**
```java
// 加密
String hashedPassword = BCrypt.hashpw(plainPassword, BCrypt.gensalt());

// 验证
boolean isMatch = BCrypt.checkpw(plainPassword, hashedPassword);
```

**敏感字段加密（AES）：**
```java
// 加密
String encryptedIdCard = AESUtils.encrypt(idCard, secretKey);

// 解密
String idCard = AESUtils.decrypt(encryptedIdCard, secretKey);
```

## 7. 脱敏检查清单

在代码提交前，必须逐项检查：

- [ ] API响应中的敏感信息已脱敏
- [ ] 日志中的敏感信息已脱敏或不记录
- [ ] 数据库中的L3级敏感信息已加密存储
- [ ] 前端展示的敏感信息已脱敏
- [ ] 文档示例中使用的是脱敏数据
- [ ] 错误提示中不包含敏感信息
- [ ] 测试数据使用的是虚拟数据，非生产数据

---

**文档版本**: 1.0
**创建日期**: 2026-03-23
**适用项目**: 所有企业级项目
