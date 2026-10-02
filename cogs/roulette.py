import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
from typing import Literal

class Roulette(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="roulette", description="Jouez à la roulette européenne.")
    async def roulette(self, interaction: discord.Interaction, mise: int, choix: Literal['rouge', 'noir', 'vert']):
        if mise <= 0:
            return await interaction.response.send_message("❌ La mise doit être supérieure à 0.", ephemeral=True)

        economie_cog = self.bot.get_cog('Economie')
        if not economie_cog:
            return await interaction.response.send_message("❌ Le module d'économie n'est pas chargé.", ephemeral=True)

        balance = await economie_cog.get_balance(interaction.user.id)
        if balance < mise:
            return await interaction.response.send_message("❌ Vous n'avez pas assez de jetons pour cette mise.", ephemeral=True)

        await economie_cog.update_balance(interaction.user.id, -mise)

        await interaction.response.send_message("🎲 **ROULETTE** 🎲\n🌀 *La roulette commence à tourner...*")
        message_obj = await interaction.original_response()

        for _ in range(3):
            await asyncio.sleep(0.8)
            temp_num = random.randint(0, 36)
            temp_c = 'rouge' if temp_num in [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36] else ('noir' if temp_num != 0 else 'vert')
            temp_e = '🔴' if temp_c == 'rouge' else '⚫' if temp_c == 'noir' else '🟢'
            await message_obj.edit(content=f"🎲 **ROULETTE** 🎲\n🌀 *La bille passe sur le **{temp_num}** {temp_e}...*")
            
        await asyncio.sleep(0.8)

        resultat = random.randint(0, 36)
        
        couleur_resultat = 'vert'
        if resultat in [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]:
            couleur_resultat = 'rouge'
        elif resultat != 0:
            couleur_resultat = 'noir'

        emoji = '🔴' if couleur_resultat == 'rouge' else '⚫' if couleur_resultat == 'noir' else '🟢'
        
        message = f"🎲 **ROULETTE** 🎲\nLa bille s'arrête sur le **{resultat} {couleur_resultat.capitalize()}** {emoji} !\n"

        if choix == couleur_resultat:
            if choix == 'vert':
                gain = mise * 35
            else:
                gain = mise * 2
            
            await economie_cog.update_balance(interaction.user.id, gain)
            message += f"\n🎉 Bien joué ! Vous avez gagné **{gain}** jetons !"
        else:
            message += "\n💸 Vous avez perdu votre mise."

        await message_obj.edit(content=message)

async def setup(bot):
    await bot.add_cog(Roulette(bot))
