import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite

class Economie(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        # Création de la table si elle n'existe pas
        await self.bot.db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                balance INTEGER DEFAULT 0
            )
        ''')
        await self.bot.db.commit()

    async def get_balance(self, user_id: int) -> int:
        async with self.bot.db.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row is None:
                await self.bot.db.execute('INSERT INTO users (user_id, balance) VALUES (?, 0)', (user_id,))
                await self.bot.db.commit()
                return 0
            return row[0]

    async def update_balance(self, user_id: int, amount: int):
        current = await self.get_balance(user_id)
        await self.bot.db.execute('UPDATE users SET balance = ? WHERE user_id = ?', (current + amount, user_id))
        await self.bot.db.commit()

    @app_commands.command(name="solde", description="Affiche votre solde de jetons.")
    async def solde(self, interaction: discord.Interaction):
        balance = await self.get_balance(interaction.user.id)
        await interaction.response.send_message(f"💰 Votre solde est de **{balance}** jetons.")

    @app_commands.command(name="daily", description="Récupérez votre récompense journalière.")
    @app_commands.checks.cooldown(1, 86400, key=lambda i: i.user.id)
    async def daily(self, interaction: discord.Interaction):
        reward = 500
        await self.update_balance(interaction.user.id, reward)
        await interaction.response.send_message(f"🎁 Vous avez reçu votre récompense journalière de **{reward}** jetons !")

    @daily.error
    async def daily_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            hours, remainder = divmod(int(error.retry_after), 3600)
            minutes, seconds = divmod(remainder, 60)
            await interaction.response.send_message(
                f"⏳ Vous devez attendre {hours}h {minutes}m {seconds}s avant de récupérer votre prochaine récompense.",
                ephemeral=True
            )

    @app_commands.command(name="give", description="Donnez des jetons à un autre joueur.")
    async def give(self, interaction: discord.Interaction, membre: discord.Member, montant: int):
        if montant <= 0:
            return await interaction.response.send_message("❌ Le montant doit être supérieur à 0.", ephemeral=True)
            
        if membre.bot:
            return await interaction.response.send_message("❌ Vous ne pouvez pas donner de jetons à un bot.", ephemeral=True)
            
        if membre.id == interaction.user.id:
            return await interaction.response.send_message("❌ Vous ne pouvez pas vous donner des jetons à vous-même.", ephemeral=True)

        sender_balance = await self.get_balance(interaction.user.id)
        if sender_balance < montant:
            return await interaction.response.send_message("❌ Vous n'avez pas assez de jetons.", ephemeral=True)

        await self.update_balance(interaction.user.id, -montant)
        await self.update_balance(membre.id, montant)
        await interaction.response.send_message(f"💸 Vous avez donné **{montant}** jetons à {membre.mention}.")

    @app_commands.command(name="classement", description="Affiche le top 10 des joueurs les plus riches.")
    async def classement(self, interaction: discord.Interaction):
        async with self.bot.db.execute('SELECT user_id, balance FROM users ORDER BY balance DESC LIMIT 10') as cursor:
            rows = await cursor.fetchall()
            
        if not rows:
            return await interaction.response.send_message("Aucun joueur n'est enregistré pour le moment.")
            
        embed = discord.Embed(title="🏆 Classement des joueurs", color=discord.Color.gold())
        
        description = ""
        for index, (user_id, balance) in enumerate(rows, start=1):
            if index == 1:
                medal = "🥇"
            elif index == 2:
                medal = "🥈"
            elif index == 3:
                medal = "🥉"
            else:
                medal = f"`{index}.`"
                
            description += f"{medal} <@{user_id}> : **{balance}** jetons\n"
            
        embed.description = description
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="addmoney", description="[Admin/Propriétaire] Injecte de l'argent sur le compte d'un joueur.")
    async def addmoney(self, interaction: discord.Interaction, membre: discord.Member, montant: int):
        is_owner = (interaction.user.id == 704385231876259920)
        is_admin = interaction.user.guild_permissions.administrator
        
        if not (is_owner or is_admin):
            return await interaction.response.send_message("❌ Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)

        if montant <= 0:
            return await interaction.response.send_message("❌ Le montant doit être supérieur à 0.", ephemeral=True)
            
        if membre.bot:
            return await interaction.response.send_message("❌ Impossible d'ajouter des jetons à un bot.", ephemeral=True)
            
        await self.update_balance(membre.id, montant)
        await interaction.response.send_message(f"🛠️ [Admin] Succès ! **{montant}** jetons ont été créés et ajoutés au solde de {membre.mention}.", ephemeral=True)

    @app_commands.command(name="removemoney", description="[Admin/Propriétaire] Retire de l'argent du compte d'un joueur.")
    async def removemoney(self, interaction: discord.Interaction, membre: discord.Member, montant: int):
        is_owner = (interaction.user.id == 704385231876259920)
        is_admin = interaction.user.guild_permissions.administrator
        
        if not (is_owner or is_admin):
            return await interaction.response.send_message("❌ Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)

        if montant <= 0:
            return await interaction.response.send_message("❌ Le montant doit être supérieur à 0.", ephemeral=True)
            
        if membre.bot:
            return await interaction.response.send_message("❌ Impossible de modifier le solde d'un bot.", ephemeral=True)
            
        balance = await self.get_balance(membre.id)
        if balance < montant:
            montant_retire = balance
        else:
            montant_retire = montant
            
        await self.update_balance(membre.id, -montant_retire)
        await interaction.response.send_message(f"🛠️ [Admin] Succès ! **{montant_retire}** jetons ont été retirés du solde de {membre.mention}.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Economie(bot))
