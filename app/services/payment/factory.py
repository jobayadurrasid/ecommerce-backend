from app.models.payment import PaymentProvider
from app.services.payment.base import PaymentStrategy
from app.services.payment.stripe import StripePaymentStrategy
from app.services.payment.bkash import BkashPaymentStrategy
from app.core.exceptions import BadRequestError


class PaymentStrategyFactory:
    _strategies = {
        PaymentProvider.STRIPE: StripePaymentStrategy,
        PaymentProvider.BKASH: BkashPaymentStrategy,
    }

    @classmethod
    def get_strategy(cls, provider: PaymentProvider | str) -> PaymentStrategy:
        if isinstance(provider, str):
            try:
                provider = PaymentProvider(provider.lower())
            except ValueError:
                raise BadRequestError(f"Unsupported payment provider: '{provider}'")

        strategy_cls = cls._strategies.get(provider)
        if not strategy_cls:
            raise BadRequestError(f"Payment strategy for '{provider}' is not implemented.")

        return strategy_cls()
