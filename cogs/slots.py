import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio

class Slots(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.emojis = ['🍒', '🍋', '🍇', '🍉', '⭐', '💎']

    @app_commands.command(name="slots", description="Jouez à la machine à sous.")
    async def slots(self, interaction: discord.Interaction, mise: int):
        if mise <= 0:
            return await interaction.response.send_message("❌ La mise doit être supérieure à 0.", ephemeral=True)

        economie_cog = self.bot.get_cog('Economie')
        if not economie_cog:
            return await interaction.response.send_message("❌ Le module d'économie n'est pas chargé.", ephemeral=True)

        balance = await economie_cog.get_balance(interaction.user.id)
        if balance < mise:
            return await interaction.response.send_message("❌ Vous n'avez pas assez de jetons pour cette mise.", ephemeral=True)

        await economie_cog.update_balance(interaction.user.id, -mise)

        await interaction.response.send_message("🎰 **SLOTS** 🎰\n🔄 | 🔄 | 🔄\n*La machine tourne...*")
        message_obj = await interaction.original_response()

        for _ in range(3):
            await asyncio.sleep(0.8)
            temp_result = [random.choice(self.emojis) for _ in range(3)]
            await message_obj.edit(content=f"🎰 **SLOTS** 🎰\n{' | '.join(temp_result)}\n*La machine tourne...*")
            
        await asyncio.sleep(0.8)
        
        result = [random.choice(self.emojis) for _ in range(3)]
        message = f"🎰 **SLOTS** 🎰\n{' | '.join(result)}\n"

        if result[0] == result[1] == result[2]:
            if result[0] == '💎':
                gain = mise * 10
                message += f"\nJACKPOT !!! 🎉 Vous gagnez **{gain}** jetons !"
            else:
                gain = mise * 2
                message += f"\nFélicitations ! Vous gagnez **{gain}** jetons !"
            await economie_cog.update_balance(interaction.user.id, gain)
        else:
            message += "\nDommage, vous avez perdu."

        await message_obj.edit(content=message)

async def setup(bot):
    await bot.add_cog(Slots(bot))
