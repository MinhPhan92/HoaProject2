from fastapi import FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy import text

from .database import Base, engine
from .routers.contracts import router as contracts_router


def create_app() -> FastAPI:
    app = FastAPI(title="HoaProject2 - Car Rental API")

    # Khởi tạo metadata ORM nếu cần (không ép create_all để tránh khác schema thực tế)
    # Base.metadata.create_all(bind=engine)

    app.include_router(contracts_router)

    @app.get("/")
    def root():
        return {
            "service": "HoaProject2 - Car Rental API",
            "endpoints": [
                "/contracts",
                "/health",
                "/docs",
                "/redoc",
            ],
        }

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/health/db")
    def health_db():
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return {"database": "ok"}
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"db_error: {exc}",
            )

    @app.get("/_debug/db", response_class=HTMLResponse)
    def debug_db(all: bool = False, limit: int = 200):
        # Render HTML danh sách toàn bộ bảng và dữ liệu (giới hạn theo limit nếu all=False)
        import html as _html

        with engine.connect() as conn:
            tables = conn.execute(
                text(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                    """
                )
            ).scalars().all()

            parts: list[str] = []
            parts.append(
                """
                <html><head><meta charset=\"utf-8\"><title>DB Dump</title>
                <style>
                body{font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Oxygen, Ubuntu, Cantarell, Helvetica, Arial, 'Apple Color Emoji','Segoe UI Emoji','Segoe UI Symbol'}
                table{border-collapse:collapse; margin:12px 0; width:100%;}
                th,td{border:1px solid #ddd; padding:6px; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;}
                th{background:#fafafa; text-align:left}
                h2{margin-top:28px}
                .meta{color:#666; font-size:13px}
                </style></head><body>
                <h1>Database Dump</h1>
                """
            )
            parts.append(f"<div class=\"meta\">tables: {len(tables)} | limit={limit} | all={all}</div>")

            for table_name in tables:
                try:
                    count = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"')).scalar_one()
                except Exception as exc:
                    parts.append(f"<h2>{_html.escape(table_name)}</h2><div class=\"meta\">count: n/a</div>")
                    parts.append(f"<pre style=\"color:#b00\">COUNT error: {_html.escape(str(exc))}</pre>")
                    continue

                parts.append(f"<h2>{_html.escape(table_name)}</h2>")
                parts.append(f"<div class=\"meta\">count: {count}</div>")

                try:
                    if all:
                        rows = conn.execute(text(f'SELECT * FROM "{table_name}"')).mappings().all()
                    else:
                        rows = conn.execute(
                            text(f'SELECT * FROM "{table_name}" LIMIT :limit'), {"limit": limit}
                        ).mappings().all()
                except Exception as exc:
                    parts.append(f"<pre style=\"color:#b00\">SELECT error: {_html.escape(str(exc))}</pre>")
                    continue

                if not rows:
                    parts.append("<div class=\"meta\">(no rows)</div>")
                    continue

                headers = list(rows[0].keys())
                parts.append("<table><thead><tr>" + "".join(f"<th>{_html.escape(str(h))}</th>" for h in headers) + "</tr></thead><tbody>")
                for r in rows:
                    parts.append("<tr>" + "".join(f"<td>{_html.escape(str(r.get(h)))}</td>" for h in headers) + "</tr>")
                parts.append("</tbody></table>")

            parts.append("</body></html>")
            return HTMLResponse("".join(parts))
    return app


app = create_app()


