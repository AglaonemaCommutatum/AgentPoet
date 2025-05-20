import google.generativeai as genai
import os
import tempfile
import subprocess
import sys
import pygame
from pygame import mixer
import gradio as gr

import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com/"

# 检查并尝试修复gradio_client
try:
    from gradio_client import Client, handle_file
except Exception as e:
    print(f"导入gradio_client时出错: {e}")
    print("尝试重新安装gradio_client...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "gradio_client==0.2.5"])
    try:
        from gradio_client import Client

        print("Gradio client重新安装并导入成功")
    except Exception as e:
        print(f"仍然存在gradio_client问题: {e}")
        exit()

# 配置API
try:
    with open("api_key.txt", "r") as f:
        genai.configure(api_key=f.readline().strip())
except FileNotFoundError:
    print("错误: 未找到'api_key.txt'文件。")
    exit()
except Exception as e:
    print(f"读取API密钥时出错: {e}")
    exit()

# 初始化模型
poetry_model = genai.GenerativeModel('gemini-1.5-flash')

# 初始化pygame混音器
pygame.init()
mixer.init()

def generate_poem(theme):
    """根据给定的主题使用语言模型生成诗歌。

    Args:
        theme: 表示诗歌主题的字符串。

    Returns:
        包含生成诗歌的字符串。
    """
    prompt = (
        f"请以「{theme}」为主题，用简体中文创作一首优美的中文诗歌。"
        "诗歌应当意境深远，语言优美，富有感情。"
        "请不要包含任何前言后语，直接返回题目内容和诗歌内容。"
        "请创作一首五言绝句或七言律诗，以文本直接输出，不带格式"
    )

    try:
        response = poetry_model.generate_content(prompt)
        poem = response.text.strip()
        print(f"生成的诗歌：\n{poem}\n")
        return poem
    except Exception as e:
        print(f"生成诗歌时出错: {e}")
        return None

def text_to_speech_api(text):
    """使用东雪莲语音API将文本转换为语音。

    Args:
        text: 要转换为语音的文本。
    """
    try:
        # 创建临时文件保存诗歌内容（虽然不再需要，但保留以备不时之需）
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp:
            temp.write(text)
            temp_filename = temp.name

        print(f"临时文件已创建: {temp_filename}")

        # 调用东雪莲语音API
        # TODO: 这里需要调参
        try:
            client = Client("CrawfordZhou/DZ-Bert-VITS2-2.3")
            result = client.predict(
                text=text,
                speaker="丁真",
                sdp_ratio=0.5,
                noise_scale=0.5,
                noise_scale_w=0.9,
                length_scale=1,
                language="ZH",
                reference_audio=handle_file(
                    'https://github.com/gradio-app/gradio/raw/main/test/test_files/audio_sample.wav'),
                emotion="Happy",
                prompt_mode="Text prompt",
                style_text=None,
                style_weight=0.7,
                api_name="/tts_fn"
            )

            # 从结果中提取音频文件路径并播放
            if isinstance(result, tuple) and len(result) > 1:
                audio_path = result[1]  # 获取音频文件路径
                return audio_path
            else:
                print(f"API返回格式异常: {result}")
                return False

        except Exception as e:
            print(f"API调用失败: {e}")
            return False

        # 清理临时文件
        try:
            os.unlink(temp_filename)
            print(f"临时文件已删除: {temp_filename}")
        except Exception as e:
            print(f"删除临时文件时出错: {e}")

        return True
    except Exception as e:
        print(f"语音生成过程中出错: {e}")
        return False

def generate_and_play(theme):
    poem = generate_poem(theme)
    audio_path = text_to_speech_api(poem) if poem else None
    return poem, audio_path

# TODO:写个gui，最好增加图像模态输入
def main():
    """运行诗歌生成器的主函数。"""
    print("=== 诗歌生成器 ===")
    print("输入一个主题，程序将生成一首相关的诗歌并朗读出来。")
    print("输入 'exit' 或 'quit' 退出程序。")

    while True:
        iface = gr.Interface(
            fn=generate_and_play,
            inputs="text",
            outputs=["text", "audio"],
            title="诗歌生成器",
            description="输入一个主题，生成相关的诗歌并播放语音。"
        )
        iface.launch()

if __name__ == "__main__":
    main()
