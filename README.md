# ForwardBot - NCatBot 消息转发插件

一个 QQ 群消息转发插件，基于 NCatBot 框架开发。支持灵活的转发规则配置、权限管理和详细的统计功能。

## 主要功能

### 核心特性

- **智能转发**：支持前缀匹配和关键词匹配两种过滤模式
- **权限管理**：基于 RBAC 的管理员权限系统
- **统计监控**：实时转发统计和成功率监控
- **安全防护**：防循环转发、重试机制、错误处理

### 转发规则支持

- **前缀匹配**：消息以指定前缀开头时触发转发
- **关键词匹配**：消息包含指定关键词时触发转发
- **多群监听**：单个规则可监听多个源群
- **多群转发**：支持同时转发到多个目标群
- **自定义前缀**：可配置转发消息的前缀模板

## 📋 项目结构

```text
forwardbot-ncatbot/
├── plugin.py                 # 主插件文件，包含所有命令处理逻辑
├── rules.py                  # 转发规则数据结构和管理器
├── forward_admin_filter.py   # 管理员权限过滤器
├── forward_config.yaml       # 配置文件
├── pyproject.toml           # 项目依赖配置
└── README.md                # 本文档
```

## 快速开始

### 环境要求

> [!NOTE]
> 请使用 `uv sync` 管理依赖

### 安装

1. 克隆项目到 NCatBot 插件目录：

    ```bash
    git clone https://github.com/KirisameVanilla/forwardbot-ncatbot.git
    ```

2. 安装依赖：

    ```bash
    uv sync  # 或 pip install -r requirements.txt
    ```

### 配置

1. 编辑 `forward_config.yaml` 文件：

    ```yaml
    # 转发机器人配置
    forward:
    enabled: true                   # 启用转发功能
    send_interval: 500              # 转发间隔(毫秒)
    
    rules:
      - name: "紧急通知转发"        # 规则名称
        enabled: true               # 启用状态
        type: "prefix"              # 匹配类型: "prefix" 或 "keyword"
        source_groups:              # 源群列表
            - 123456789
        target_groups:              # 目标群列表
            - 987654321
            - 555666777
        keywords:                   # 匹配关键词
            - "【紧急】"
            - "【重要】"
        forward_full_message: true  # 转发完整消息
        preserve_format: true       # 保持原格式
        forward_prefix: "[转发来自群{source_group}]"  # 转发前缀

    # 管理员配置
    admin:
        - 123456789                     # 管理员QQ号
    ```

2. 在 NCatBot 中加载插件, 可以参照 [NVanillaaaaBot](https://github.com/kirisamevanilla/nvanillaaaabot)

## 使用指南

### 命令系统

本插件使用 NCatBot 的现代化命令系统，支持参数、选项和灵活的命令语法。

### 统计查看命令

```bash
/forward stats                    # 查看基本统计信息
/forward stats -v                 # 查看详细统计信息
/forward stats --verbose          # 查看详细统计信息（完整形式）
```

统计信息包括：

- 转发成功/失败次数和成功率
- 规则数量统计（总数、启用、禁用）
- 监听群数和目标群数
- 运行时间等详细信息

### 规则管理命令

#### 查看规则列表

```bash
/forward rules list               # 查看简单格式的规则列表  
/forward rules list -d            # 查看详细格式的规则列表
/forward rules list --detailed    # 查看详细格式的规则列表（完整形式）
```

#### 规则操作（需要管理员权限）

```bash
/forward rules enable <规则名>     # 启用规则
/forward rules disable <规则名>    # 禁用规则
/forward rules delete <规则名>     # 删除规则（需要二次确认）
/forward rules delete <规则名> -f  # 强制删除规则
/forward rules delete <规则名> --force  # 强制删除规则（完整形式）
```

### 管理员管理命令（需要超级管理员权限）

```bash
/forward admins add <QQ号>        # 添加转发管理员
```

## 配置详解

### 规则配置说明

每个转发规则包含以下配置项：

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `name` | string | 规则名称（唯一标识） | "紧急通知转发" |
| `enabled` | boolean | 是否启用此规则 | true |
| `type` | string | 匹配类型："prefix" 或 "keyword" | "prefix" |
| `source_groups` | array | 监听的源群号列表 | [123456789] |
| `target_groups` | array | 转发目标群号列表 | [987654321] |
| `keywords` | array | 匹配的关键词/前缀列表 | ["【紧急】", "【重要】"] |
| `forward_full_message` | boolean | 是否转发完整消息 | true |
| `preserve_format` | boolean | 是否保持原始格式 | true |
| `forward_prefix` | string | 转发前缀模板 | "[转发]" |

### 前缀模板变量

转发前缀支持以下变量：

- `{source_group}`: 源群号
- `{sender}`: 发送者昵称
- `{rule_name}`: 规则名称

示例：`"[转发来自群{source_group}] {sender}: "`

## 权限系统

### 权限级别

1. **超级管理员**：拥有所有权限，可以添加/删除转发管理员
2. **转发管理员**：可以管理转发规则（增删改查、启用/禁用）
3. **普通用户**：只能查看统计信息和规则列表

### 权限配置

在 `forward_config.yaml` 中配置管理员：

```yaml
admin:
  - 123456789  # 管理员QQ号
  - 987654321
```

或通过命令动态添加：

```bash
/forward admins add 123456789
```

## 安全特性

### 防循环转发

- 自动检测并阻止消息转发回源群
- 智能识别机器人自身发送的消息并过滤

### 错误处理与重试

- 转发失败自动重试（最多2次）
- 详细的错误日志记录
- 优雅处理群不存在、权限不足等异常

### 频率控制

- 可配置转发间隔防止频率过快
- 统计转发成功率便于监控

## 监控与日志

### 统计信息

- 实时转发成功/失败计数
- 转发成功率统计
- 规则使用情况统计
- 运行时长监控

### 日志记录

- 详细的转发过程日志
- 错误异常日志
- 权限操作审计日志
- 规则变更日志

## 开发指南

### 核心类说明

#### `ForwardBotPlugin`

主插件类，处理所有命令和消息转发逻辑。

#### `ForwardRuleManager`

规则管理器，负责规则的增删改查和配置文件管理。

#### `ForwardRule`

转发规则数据类，定义规则的所有属性和行为。

#### `ForwardAdminFilter`

管理员权限过滤器，集成 NCatBot 的 RBAC 系统。

### 自定义开发

1. 扩展规则类型：在 `RuleType` 枚举中添加新类型
2. 自定义匹配逻辑：修改 `ForwardRule.matches_message()` 方法
3. 添加新命令：在 `ForwardBotPlugin` 中使用装饰器语法添加
