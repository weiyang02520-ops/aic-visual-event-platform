# 第三方许可证清单（阶段性）

本清单用于提交暂存包的来源说明，不替代正式法律审查。最终打包时应根据锁定版本生成完整依赖树和许可证文本。

## Python

- FastAPI、Uvicorn、Pydantic：AI REST 服务运行依赖；
- python-multipart：表单/文件解析预留；
- pytest、httpx：测试依赖；
- NumPy、OpenCV、Pillow：可选本地帧/图像能力，当前没有把二进制或模型权重放入包。

## JavaScript

- React、React DOM：前端 UI；
- Vite、TypeScript：开发和构建；
- lucide-react：图标；
- @types/react、@types/react-dom：开发类型。

各依赖的具体许可证应以对应锁定版本的上游 LICENSE 和包元数据为准。提交包不包含 `node_modules`，因此不会把依赖目录误当作项目源码交付。
