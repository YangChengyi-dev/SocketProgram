from flask import Flask, send_file, abort
import os

app = Flask(__name__)

# 要分发的文件路径（可自行修改）
FILE_PATH = "D:\ProjectTraeAI\Experiment1234\Experiment1234\digital_product\ebook_test.pdf"

@app.route("/download", methods=["GET"])
def download_file():
    """
    HTTP 文件分发接口
    URL: /download
    """
    if not os.path.exists(FILE_PATH):
        abort(404, description="File not found")

    return send_file(
        FILE_PATH,
        as_attachment=True,
        download_name=os.path.basename(FILE_PATH)
    )

if __name__ == "__main__":
    # 监听 0.0.0.0:8080
    app.run(host="0.0.0.0", port=8080)
