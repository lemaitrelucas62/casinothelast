import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio

class BlackjackView(discord.ui.View):
    def __init__(self, bot, user, mise, deck):
        super().__init__(timeout=60.0)
        self.bot = bot
        self.user = user
        self.mise = mise
        self.deck = deck
        self.player_hand = []
        self.dealer_hand = []
        self.economie_cog = self.bot.get_cog('Economie')
        
        # Initialisation des mains
        self.player_hand.append(self.draw_card())
        self.dealer_hand.append(self.draw_card())
        self.player_hand.append(self.draw_card())
        self.dealer_hand.append(self.draw_card())

    def draw_card(self):
        return self.deck.pop(random.randint(0, len(self.deck) - 1))

    def calculate_score(self, hand):
        score = 0
        aces = 0
        for card in hand:
            if card in ['J', 'Q', 'K']:
                score += 10
            elif card == 'A':
                aces += 1
                score += 11
            else:
                score += int(card)
        
        while score > 21 and aces:
            score -= 10
            aces -= 1
            
        return score

    def format_hand(self, hand, hide_second=False):
        if hide_second and len(hand) == 2:
            return f"{hand[0]} et [Cachée]"
        return " - ".join(hand)

    def generate_embed(self, game_over=False, result_msg=""):
        embed = discord.Embed(title="🃏 Blackjack", color=discord.Color.gold())
        
        dealer_score = self.calculate_score(self.dealer_hand)
        player_score = self.calculate_score(self.player_hand)
        
        if game_over:
            embed.add_field(name="Main du Croupier", value=f"{self.format_hand(self.dealer_hand)}\nScore: {dealer_score}", inline=False)
        else:
            embed.add_field(name="Main du Croupier", value=f"{self.format_hand(self.dealer_hand, hide_second=True)}\nScore: ?", inline=False)
            
        embed.add_field(name="Votre Main", value=f"{self.format_hand(self.player_hand)}\nScore: {player_score}", inline=False)
        
        if result_msg:
            embed.add_field(name="Résultat", value=result_msg, inline=False)
            
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.user:
            await interaction.response.send_message("❌ Ce n'est pas votre partie !", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(content="⏳ Le temps est écoulé, vous avez perdu par forfait.", view=self)
        except:
            pass

    @discord.ui.button(label="Tirer", style=discord.ButtonStyle.primary)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.player_hand.append(self.draw_card())
        player_score = self.calculate_score(self.player_hand)
        
        if player_score > 21:
            for item in self.children:
                item.disabled = True
            self.stop()
            embed = self.generate_embed(game_over=True, result_msg="Vous avez dépassé 21. Vous avez perdu.")
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            embed = self.generate_embed()
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Rester", style=discord.ButtonStyle.secondary)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        self.stop()
        
        dealer_score = self.calculate_score(self.dealer_hand)
        while dealer_score < 17:
            self.dealer_hand.append(self.draw_card())
            dealer_score = self.calculate_score(self.dealer_hand)
            
        player_score = self.calculate_score(self.player_hand)
        
        result_msg = ""
        if dealer_score > 21:
            result_msg = f"Le croupier a dépassé 21. Vous gagnez **{self.mise * 2}** jetons !"
            await self.economie_cog.update_balance(self.user.id, self.mise * 2)
        elif player_score > dealer_score:
            result_msg = f"Vous avez battu le croupier. Vous gagnez **{self.mise * 2}** jetons !"
            await self.economie_cog.update_balance(self.user.id, self.mise * 2)
        elif player_score < dealer_score:
            result_msg = "Le croupier vous a battu. Vous perdez votre mise."
        else:
            result_msg = "Égalité. Vous récupérez votre mise."
            await self.economie_cog.update_balance(self.user.id, self.mise)
            
        embed = self.generate_embed(game_over=True, result_msg=result_msg)
        await interaction.response.edit_message(embed=embed, view=self)

class Blackjack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.base_deck = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'] * 4

    @app_commands.command(name="blackjack", description="Jouez au Blackjack contre le croupier.")
    async def blackjack(self, interaction: discord.Interaction, mise: int):
        if mise <= 0:
            return await interaction.response.send_message("❌ La mise doit être supérieure à 0.", ephemeral=True)

        economie_cog = self.bot.get_cog('Economie')
        if not economie_cog:
            return await interaction.response.send_message("❌ Le module d'économie n'est pas chargé.", ephemeral=True)

        balance = await economie_cog.get_balance(interaction.user.id)
        if balance < mise:
            return await interaction.response.send_message("❌ Vous n'avez pas assez de jetons pour cette mise.", ephemeral=True)

        # On débite la mise dès le début
        await economie_cog.update_balance(interaction.user.id, -mise)

        deck = list(self.base_deck)
        view = BlackjackView(self.bot, interaction.user, mise, deck)
        
        player_score = view.calculate_score(view.player_hand)
        
        # Vérification blackjack naturel
        if player_score == 21:
            dealer_score = view.calculate_score(view.dealer_hand)
            if dealer_score == 21:
                # Egalite
                await economie_cog.update_balance(interaction.user.id, mise)
                embed = view.generate_embed(game_over=True, result_msg="Double Blackjack ! Égalité, vous récupérez votre mise.")
            else:
                # Gain blackjack (généralement 3:2 donc x2.5 avec la mise)
                gain = int(mise * 2.5)
                await economie_cog.update_balance(interaction.user.id, gain)
                embed = view.generate_embed(game_over=True, result_msg=f"BLACKJACK ! Vous gagnez **{gain}** jetons !")
            
            for item in view.children:
                item.disabled = True
            await interaction.response.send_message(embed=embed, view=view)
            return

        embed = view.generate_embed()
        await interaction.response.send_message(embed=embed, view=view)
        view.message = await interaction.original_response()

async def setup(bot):
    await bot.add_cog(Blackjack(bot))
