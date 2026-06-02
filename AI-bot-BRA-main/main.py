import discord
from discord.ext import commands
from model import get_class
import os
import random
import requests
from PIL import Image
import numpy as np

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='$', intents=intents)

# ==================== VARIÁVEIS GLOBAIS ====================
current_car = None
current_car_name = None

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

# ==================== COMANDO DUCK (já existia) ====================
def get_duck_image_url():
    url = 'https://random-d.uk/api/random'
    res = requests.get(url)
    data = res.json()
    return data['url']

@bot.command('duck')
async def duck(ctx):
    image_url = get_duck_image_url()
    await ctx.send(image_url)

# ==================== 1. COMANDO DE MOEDAS ====================
@bot.command()
async def moedas(ctx, moeda_base: str = "BRL"):
    """Mostra valores de moedas"""
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{moeda_base.upper()}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if response.status_code != 200 or "rates" not in data:
            await ctx.send(f"❌ Moeda inválida ou erro na API.")
            return
            
        rates = data["rates"]
        
        # Conversão segura para float
        usd = float(rates.get('USD', 0))
        eur = float(rates.get('EUR', 0))
        btc = float(rates.get('BTC', 0))
        
        embed = discord.Embed(title=f"💱 Taxas de Câmbio - {moeda_base.upper()}", color=0x00ff00)
        embed.add_field(name="USD", value=f"R$ {usd:.2f}", inline=True)
        embed.add_field(name="EUR", value=f"R$ {eur:.2f}", inline=True)
        embed.add_field(name="BTC", value=f"R$ {btc:.2f}", inline=True)
        embed.set_footer(text="Fonte: ExchangeRate-API")
        
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Erro ao buscar moedas: {str(e)}")
# ==================== 2. COMANDO QUANTAS CORES ====================
@bot.command(name="quantascores")
async def quantas_cores(ctx):
    """Conta quantas cores únicas tem na imagem enviada"""
    if not ctx.message.attachments:
        await ctx.send("❌ Você precisa enviar uma imagem junto com o comando `$quantascores`!")
        return

    attachment = ctx.message.attachments[0]
    filename = f"./temp_{attachment.filename}"
    
    await attachment.save(filename)
    
    try:
        img = Image.open(filename).convert("RGB")
        img_array = np.array(img)
        pixels = img_array.reshape(-1, 3)
        unique_colors = len(np.unique(pixels, axis=0))
        
        await ctx.send(f"🎨 **Essa imagem tem `{unique_colors:,}` cores únicas!**")
    except Exception as e:
        await ctx.send("❌ Erro ao processar a imagem.")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

# ==================== 3. JOGO DE ADIVINHAR CARROS ====================
@bot.command()
async def iniciarcarro(ctx):
    """Inicia o jogo de adivinhar o carro"""
    global current_car, current_car_name
    
    car_folder = "car_images"
    
    if not os.path.exists(car_folder) or not os.listdir(car_folder):
        await ctx.send("❌ Crie a pasta `car_images` e coloque imagens de carros!")
        return
    
    # Adicionado suporte para .jfif
    car_list = [f for f in os.listdir(car_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.jfif'))]
    
    if not car_list:
        await ctx.send("❌ Nenhuma imagem válida encontrada na pasta `car_images`!\n"
                      "Coloque imagens com extensão .jpg, .jpeg, .png ou .jfif")
        return
    
    current_car = random.choice(car_list)
    current_car_name = os.path.splitext(current_car)[0].replace("_", " ").title()
    
    await ctx.send("🚗 **Jogo de Adivinhar Carro Iniciado!**")
    await ctx.send("Qual é esse carro?")
    await ctx.send(file=discord.File(f"{car_folder}/{current_car}"))

# ==================== EVENTO ON_MESSAGE (para o jogo) ====================
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    global current_car, current_car_name

    # Verifica resposta do jogo
    if current_car and current_car_name:
        resposta = message.content.lower()
        nome_carro = current_car_name.lower()
        
        if nome_carro in resposta or resposta in nome_carro:
            await message.channel.send(f"✅ **Parabéns {message.author.mention}!** Você acertou! Era **{current_car_name}**.")
            current_car = None
            current_car_name = None
            return

    # Processa comandos normalmente
    await bot.process_commands(message)

# ==================== COMANDO CHECK (mantido) ====================
@bot.command()
async def check(ctx):
    if ctx.message.attachments:
        for attachment in ctx.message.attachments:
            await attachment.save(f"./{attachment.filename}")
            resultado = get_class(
                model_path="./keras_model.h5", 
                labels_path="labels.txt", 
                image_path=f"./{attachment.filename}"
            )
            await ctx.send(resultado)
    else:
        await ctx.send("You forgot to upload the image :(")

# ==================== RODAR O BOT ====================
bot.run('SEU TOKEN')   # ← Troque pelo seu token