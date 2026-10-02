import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import aiosqlite

# Chargement des variables d'environnement
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Configuration des intents
intents = discord.Intents.default()

class CasinoBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents)
        self.db = None

    async def setup_hook(self):
        # Initialisation de la connexion à la base de données
        self.db = await aiosqlite.connect('database.db')
        
        # Chargement des cogs
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
                print(f'Cog chargé: {filename}')
        
        # Synchronisation des slash commands
        await self.tree.sync()
        print('Slash commands synchronisées.')

    async def on_ready(self):
        print(f'Connecté en tant que {self.user} (ID: {self.user.id})')
        print('------')

    async def close(self):
        if self.db:
            await self.db.close()
        await super().close()

bot = CasinoBot()

if __name__ == '__main__':
    if not TOKEN:
        print("Erreur: Le token n'est pas défini dans les variables d'environnement ou le fichier .env")
    else:
        bot.run(TOKEN)
