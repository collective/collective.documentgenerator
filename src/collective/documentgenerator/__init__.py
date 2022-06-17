# -*- coding: utf-8 -*-
"""Init and utils."""

from AccessControl.ZopeGuards import get_safe_globals
from AccessControl.ZopeGuards import guarded_getattr
from appy.pod import actions
from appy.pod import elements
from RestrictedPython import compile_restricted
from zope.i18nmessageid import MessageFactory
from appy.pod import Evaluator


_ = MessageFactory('collective.documentgenerator')


def initialize(context):
    """Initializer called when used as a Zope 2 product."""


def _restricted_evalExpr(self, expr, context):
    '''Evaluates p_expr with p_context. p_expr can contain an error expr,
        in the form "someExpr|errorExpr". If it is the case, if the "normal"
        expr raises an error, the "error" expr is evaluated instead.'''

    # XXX for the "view" methods to be accessible, we need to decorate the
    # methods with @security.protected('View') or security.delcarePublic('View', 'method_name')

    context.update(get_safe_globals())
    context['_getattr_'] = guarded_getattr

    if '|' not in expr:
        res = eval(compile_restricted(expr, '<string>', 'eval'), context)
    else:
        expr, errorExpr = expr.rsplit('|', 1)
        try:
            res = eval(compile_restricted(expr, '<string>', 'eval'), context)
        except Exception:
            res = eval(compile_restricted(expr, '<string>', 'eval'), context)
    return res


def _restricted_eval(self, context):
    '''Evaluates self.expr with p_context. If self.errorExpr is defined,
        evaluate it if self.expr raises an error.'''

    # XXX for the "view" methods to be accessible, we need to decorate the
    # methods with @security.protected('View') or security.delcarePublic('View', 'method_name')

    context.update(get_safe_globals())
    context['_getattr_'] = guarded_getattr

    if self.errorExpr:
        try:
            res = eval(compile_restricted(self.expr, '<string>', 'eval'), context)
        except Exception:
            res = eval(compile_restricted(self.errorExpr, '<string>', 'eval'), context)
    else:
        res = eval(compile_restricted(self.expr, '<string>', 'eval'), context)
    return res


_Evaluator_old_run = Evaluator.run

@classmethod
def run(class_, expression, context):
    ''' '''

    # XXX for the "view" methods to be accessible, we need to decorate the
    # methods with @security.protected('View') or security.delcarePublic('View', 'method_name')
    context.update(get_safe_globals())
    context['_getattr_'] = guarded_getattr
    return eval(compile_restricted(expression, '<string>', 'eval'), context)


Evaluator.run = run

#actions.Action._evalExpr = _restricted_evalExpr
#elements.Expression._eval = _restricted_eval
