import google.generativeai as genai
import os
import tempfile
import subprocess
import sys
import pygame
from pygame import mixer

# 检查并尝试修复gradio_client
try:
    from gradio_client import Client

    print("Gradio client导入成功")
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
        "请不要包含任何前言后语，直接返回诗歌的标题和内容。"
        "请创作一首五言绝句或七言律诗"
    )

    try:
        response = poetry_model.generate_content(prompt)
        poem = response.text.strip()
        print(f"生成的诗歌：\n{poem}\n")
        return poem
    except Exception as e:
        print(f"生成诗歌时出错: {e}")
        return None


def play_audio(audio_path):
    """播放指定路径的音频文件。

    Args:
        audio_path: 音频文件的路径。
    """
    try:
        print(f"正在播放音频: {audio_path}")
        sound = mixer.Sound(audio_path)
        duration = int(sound.get_length() * 1000)
        sound.play()
        pygame.time.wait(duration)
        print("音频播放完成")
        return True
    except Exception as e:
        print(f"播放音频时出错: {e}")
        return False


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
        try:
            print("正在调用东雪莲API生成语音...")
            client = Client("https://leafleafleaf-azuma-bert-vits2-0-2.hf.space/--replicas/wy9ux/")
            result = client.predict(
                text,  # 输入文本内容
                "东雪莲",  # 选择说话人
                0.3,  # SDP/DP混合比
                0.9,  # 感情
                0.5,  # 音素长度
                2,  # 语速
                "ZH",  # 选择语言
                api_name="/tts_fn"
            )
            print(f"API返回结果: {result}")

            # 从结果中提取音频文件路径并播放
            if isinstance(result, tuple) and len(result) > 1:
                audio_path = result[1]  # 获取音频文件路径
                play_audio(audio_path)
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


def main():
    """运行诗歌生成器的主函数。"""
    print("=== 诗歌生成器 ===")
    print("输入一个主题，程序将生成一首相关的诗歌并朗读出来。")
    print("输入 'exit' 或 'quit' 退出程序。")

    while True:
        theme = input("\n请输入诗歌主题: ")
        if theme.lower() in ["exit", "quit"]:
            print("程序已退出。")
            break

        # 生成诗歌
        poem = generate_poem(theme)
        if poem:
            # 使用东雪莲API转换诗歌为语音
            print("正在生成语音...")
            text_to_speech_api(poem)


if __name__ == "__main__":
    main()