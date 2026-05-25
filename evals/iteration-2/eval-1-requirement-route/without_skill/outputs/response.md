# 文件上传功能 — 实现方案

## 需求理解

你要给内部管理系统加一个文件上传模块，核心要点：

| 要素 | 说明 |
|------|------|
| 交互方式 | 拖拽上传 + 点击上传 |
| 文件大小限制 | 单文件最大 50MB |
| 后续操作 | 列表预览、删除 |
| 技术栈 | Next.js 前端 + Express 后端 |
| 存储方式 | 本地磁盘 |
| 时间要求 | 本周内 |

---

## 前端实现（Next.js）

### 1. 拖拽上传组件

```tsx
// components/FileUpload.tsx
'use client';

import { useState, useCallback, useRef } from 'react';

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  url: string;
  uploadedAt: string;
}

export default function FileUpload() {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 上传单个文件
  const uploadFile = async (file: File) => {
    if (file.size > MAX_FILE_SIZE) {
      throw new Error(`文件 ${file.name} 超过 50MB 限制`);
    }

    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch('/api/upload', {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.error || '上传失败');
    }

    return res.json();
  };

  // 处理文件列表
  const handleFiles = useCallback(async (fileList: FileList | File[]) => {
    setError(null);
    setUploading(true);

    const results: UploadedFile[] = [];
    const errors: string[] = [];

    for (const file of Array.from(fileList)) {
      try {
        const result = await uploadFile(file);
        results.push(result.file);
      } catch (err: any) {
        errors.push(err.message);
      }
    }

    setFiles((prev) => [...prev, ...results]);
    if (errors.length > 0) {
      setError(errors.join('; '));
    }
    setUploading(false);
  }, []);

  // 拖拽事件
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    if (e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  };

  // 删除文件
  const deleteFile = async (id: string) => {
    const res = await fetch(`/api/upload/${id}`, { method: 'DELETE' });
    if (res.ok) {
      setFiles((prev) => prev.filter((f) => f.id !== id));
    }
  };

  // 格式化文件大小
  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  // 根据文件类型返回预览
  const renderPreview = (file: UploadedFile) => {
    if (file.type.startsWith('image/')) {
      return <img src={file.url} alt={file.name} className="w-16 h-16 object-cover rounded" />;
    }
    if (file.type === 'application/pdf') {
      return <div className="w-16 h-16 bg-red-100 rounded flex items-center justify-center text-red-600 text-xs">PDF</div>;
    }
    return <div className="w-16 h-16 bg-gray-100 rounded flex items-center justify-center text-gray-600 text-xs">FILE</div>;
  };

  return (
    <div className="p-6">
      {/* 拖拽区域 */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
          ${dragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}`}
      >
        <p className="text-gray-600">
          {uploading ? '上传中...' : '拖拽文件到此处，或点击选择文件'}
        </p>
        <p className="text-gray-400 text-sm mt-1">单文件最大 50MB</p>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          onChange={(e) => e.target.files && handleFiles(e.target.files)}
          className="hidden"
        />
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="mt-4 p-3 bg-red-50 text-red-700 rounded">{error}</div>
      )}

      {/* 文件列表 */}
      {files.length > 0 && (
        <div className="mt-6 space-y-2">
          <h3 className="font-medium text-gray-800">已上传文件</h3>
          {files.map((file) => (
            <div key={file.id} className="flex items-center gap-3 p-3 bg-white border rounded-lg">
              {renderPreview(file)}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{file.name}</p>
                <p className="text-xs text-gray-500">{formatSize(file.size)}</p>
              </div>
              <a
                href={file.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 text-sm hover:underline"
              >
                预览
              </a>
              <button
                onClick={() => deleteFile(file.id)}
                className="text-red-500 text-sm hover:underline"
              >
                删除
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

### 2. Next.js API Route（转发到 Express 后端）

```ts
// app/api/upload/route.ts
import { NextRequest, NextResponse } from 'next/server';

const EXPRESS_BACKEND = process.env.BACKEND_URL || 'http://localhost:3001';

export async function POST(req: NextRequest) {
  const formData = await req.formData();
  const file = formData.get('file') as File;

  if (!file) {
    return NextResponse.json({ error: '未选择文件' }, { status: 400 });
  }

  if (file.size > 50 * 1024 * 1024) {
    return NextResponse.json({ error: '文件超过 50MB 限制' }, { status: 400 });
  }

  // 转发到 Express 后端
  const backendForm = new FormData();
  backendForm.append('file', file);

  const res = await fetch(`${EXPRESS_BACKEND}/api/upload`, {
    method: 'POST',
    body: backendForm,
  });

  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}

export async function DELETE(req: NextRequest) {
  const id = req.nextUrl.pathname.split('/').pop();
  const res = await fetch(`${EXPRESS_BACKEND}/api/upload/${id}`, {
    method: 'DELETE',
  });
  return NextResponse.json(await res.json(), { status: res.status });
}
```

---

## 后端实现（Express）

```ts
// server.ts
import express from 'express';
import multer from 'multer';
import path from 'path';
import fs from 'fs';
import crypto from 'crypto';
import cors from 'cors';

const app = express();
const PORT = 3001;
const UPLOAD_DIR = path.join(__dirname, 'uploads');
const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

// 确保上传目录存在
if (!fs.existsSync(UPLOAD_DIR)) {
  fs.mkdirSync(UPLOAD_DIR, { recursive: true });
}

app.use(cors());
app.use(express.json());

// 文件元数据存储（生产环境建议用数据库）
interface FileRecord {
  id: string;
  name: string;
  size: number;
  type: string;
  storedName: string;
  uploadedAt: string;
}
const fileStore = new Map<string, FileRecord>();

// multer 配置
const storage = multer.diskStorage({
  destination: UPLOAD_DIR,
  filename: (_req, file, cb) => {
    // 用随机名避免冲突
    const ext = path.extname(file.originalname);
    const storedName = `${crypto.randomUUID()}${ext}`;
    cb(null, storedName);
  },
});

const upload = multer({
  storage,
  limits: { fileSize: MAX_FILE_SIZE },
});

// 上传接口
app.post('/api/upload', upload.single('file'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: '未选择文件' });
  }

  const id = crypto.randomUUID();
  const record: FileRecord = {
    id,
    name: req.file.originalname,
    size: req.file.size,
    type: req.file.mimetype,
    storedName: req.file.filename,
    uploadedAt: new Date().toISOString(),
  };

  fileStore.set(id, record);

  res.json({
    file: {
      id,
      name: record.name,
      size: record.size,
      type: record.type,
      url: `/api/upload/${id}`,
      uploadedAt: record.uploadedAt,
    },
  });
});

// 文件预览/下载
app.get('/api/upload/:id', (req, res) => {
  const record = fileStore.get(req.params.id);
  if (!record) {
    return res.status(404).json({ error: '文件不存在' });
  }

  const filePath = path.join(UPLOAD_DIR, record.storedName);
  if (!fs.existsSync(filePath)) {
    return res.status(404).json({ error: '文件已丢失' });
  }

  res.setHeader('Content-Type', record.type);
  res.setHeader('Content-Disposition', `inline; filename="${encodeURIComponent(record.name)}"`);
  fs.createReadStream(filePath).pipe(res);
});

// 删除文件
app.delete('/api/upload/:id', (req, res) => {
  const record = fileStore.get(req.params.id);
  if (!record) {
    return res.status(404).json({ error: '文件不存在' });
  }

  const filePath = path.join(UPLOAD_DIR, record.storedName);
  if (fs.existsSync(filePath)) {
    fs.unlinkSync(filePath);
  }

  fileStore.delete(req.params.id);
  res.json({ success: true });
});

app.listen(PORT, () => {
  console.log(`文件上传服务运行在 http://localhost:${PORT}`);
});
```

---

## 实现步骤（按天拆排）

| 天 | 任务 |
|----|------|
| Day 1 | 搭建 Express 后端：multer 配置、上传/删除/预览三个接口 |
| Day 2 | 前端拖拽组件 + API Route 转发，联调上传和列表展示 |
| Day 3 | 预览功能（图片缩略图、PDF 内嵌、其他文件下载）、删除确认、错误处理 |

---

## 需要关注的点

1. **安全**：当前是内部系统，但建议加一个简单的鉴权中间件，防止未授权上传
2. **文件类型校验**：如果需要限制可上传的文件类型，在 multer 的 `fileFilter` 里加白名单
3. **持久化**：上面用 Map 存元数据，重启会丢失。如果要持久化，改用 SQLite 或 JSON 文件存储
4. **大文件上传**：50MB 用单次上传没问题。如果以后要支持更大文件，考虑分片上传
5. **磁盘空间**：本地磁盘存储要注意监控空间，可以加一个定期清理策略

需要我直接开始写代码，还是你想先确认一下方案？
