// Generated from c:/Users/santi/Desktop/peak-acl/grammar/ACL.g4 by ANTLR 4.13.1
import org.antlr.v4.runtime.atn.*;
import org.antlr.v4.runtime.dfa.DFA;
import org.antlr.v4.runtime.*;
import org.antlr.v4.runtime.misc.*;
import org.antlr.v4.runtime.tree.*;
import java.util.List;
import java.util.Iterator;
import java.util.ArrayList;

@SuppressWarnings({"all", "warnings", "unchecked", "unused", "cast", "CheckReturnValue"})
public class ACLParser extends Parser {
	static { RuntimeMetaData.checkVersion("4.13.1", RuntimeMetaData.VERSION); }

	protected static final DFA[] _decisionToDFA;
	protected static final PredictionContextCache _sharedContextCache =
		new PredictionContextCache();
	public static final int
		LPAREN=1, RPAREN=2, COLON=3, STRING=4, SYMBOL=5, WS=6;
	public static final int
		RULE_message = 0, RULE_performative = 1, RULE_param = 2, RULE_value = 3;
	private static String[] makeRuleNames() {
		return new String[] {
			"message", "performative", "param", "value"
		};
	}
	public static final String[] ruleNames = makeRuleNames();

	private static String[] makeLiteralNames() {
		return new String[] {
			null, "'('", "')'", "':'"
		};
	}
	private static final String[] _LITERAL_NAMES = makeLiteralNames();
	private static String[] makeSymbolicNames() {
		return new String[] {
			null, "LPAREN", "RPAREN", "COLON", "STRING", "SYMBOL", "WS"
		};
	}
	private static final String[] _SYMBOLIC_NAMES = makeSymbolicNames();
	public static final Vocabulary VOCABULARY = new VocabularyImpl(_LITERAL_NAMES, _SYMBOLIC_NAMES);

	/**
	 * @deprecated Use {@link #VOCABULARY} instead.
	 */
	@Deprecated
	public static final String[] tokenNames;
	static {
		tokenNames = new String[_SYMBOLIC_NAMES.length];
		for (int i = 0; i < tokenNames.length; i++) {
			tokenNames[i] = VOCABULARY.getLiteralName(i);
			if (tokenNames[i] == null) {
				tokenNames[i] = VOCABULARY.getSymbolicName(i);
			}

			if (tokenNames[i] == null) {
				tokenNames[i] = "<INVALID>";
			}
		}
	}

	@Override
	@Deprecated
	public String[] getTokenNames() {
		return tokenNames;
	}

	@Override

	public Vocabulary getVocabulary() {
		return VOCABULARY;
	}

	@Override
	public String getGrammarFileName() { return "ACL.g4"; }

	@Override
	public String[] getRuleNames() { return ruleNames; }

	@Override
	public String getSerializedATN() { return _serializedATN; }

	@Override
	public ATN getATN() { return _ATN; }

	public ACLParser(TokenStream input) {
		super(input);
		_interp = new ParserATNSimulator(this,_ATN,_decisionToDFA,_sharedContextCache);
	}

	@SuppressWarnings("CheckReturnValue")
	public static class MessageContext extends ParserRuleContext {
		public MessageContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_message; }
	 
		public MessageContext() { }
		public void copyFrom(MessageContext ctx) {
			super.copyFrom(ctx);
		}
	}
	@SuppressWarnings("CheckReturnValue")
	public static class ACLmessageContext extends MessageContext {
		public TerminalNode LPAREN() { return getToken(ACLParser.LPAREN, 0); }
		public PerformativeContext performative() {
			return getRuleContext(PerformativeContext.class,0);
		}
		public TerminalNode RPAREN() { return getToken(ACLParser.RPAREN, 0); }
		public List<ParamContext> param() {
			return getRuleContexts(ParamContext.class);
		}
		public ParamContext param(int i) {
			return getRuleContext(ParamContext.class,i);
		}
		public ACLmessageContext(MessageContext ctx) { copyFrom(ctx); }
	}

	public final MessageContext message() throws RecognitionException {
		MessageContext _localctx = new MessageContext(_ctx, getState());
		enterRule(_localctx, 0, RULE_message);
		int _la;
		try {
			_localctx = new ACLmessageContext(_localctx);
			enterOuterAlt(_localctx, 1);
			{
			setState(8);
			match(LPAREN);
			setState(9);
			performative();
			setState(13);
			_errHandler.sync(this);
			_la = _input.LA(1);
			while (_la==COLON) {
				{
				{
				setState(10);
				param();
				}
				}
				setState(15);
				_errHandler.sync(this);
				_la = _input.LA(1);
			}
			setState(16);
			match(RPAREN);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	@SuppressWarnings("CheckReturnValue")
	public static class PerformativeContext extends ParserRuleContext {
		public PerformativeContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_performative; }
	 
		public PerformativeContext() { }
		public void copyFrom(PerformativeContext ctx) {
			super.copyFrom(ctx);
		}
	}
	@SuppressWarnings("CheckReturnValue")
	public static class ACLperformativeContext extends PerformativeContext {
		public TerminalNode SYMBOL() { return getToken(ACLParser.SYMBOL, 0); }
		public ACLperformativeContext(PerformativeContext ctx) { copyFrom(ctx); }
	}

	public final PerformativeContext performative() throws RecognitionException {
		PerformativeContext _localctx = new PerformativeContext(_ctx, getState());
		enterRule(_localctx, 2, RULE_performative);
		try {
			_localctx = new ACLperformativeContext(_localctx);
			enterOuterAlt(_localctx, 1);
			{
			setState(18);
			match(SYMBOL);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	@SuppressWarnings("CheckReturnValue")
	public static class ParamContext extends ParserRuleContext {
		public ParamContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_param; }
	 
		public ParamContext() { }
		public void copyFrom(ParamContext ctx) {
			super.copyFrom(ctx);
		}
	}
	@SuppressWarnings("CheckReturnValue")
	public static class ACLparamContext extends ParamContext {
		public TerminalNode COLON() { return getToken(ACLParser.COLON, 0); }
		public TerminalNode SYMBOL() { return getToken(ACLParser.SYMBOL, 0); }
		public ValueContext value() {
			return getRuleContext(ValueContext.class,0);
		}
		public ACLparamContext(ParamContext ctx) { copyFrom(ctx); }
	}

	public final ParamContext param() throws RecognitionException {
		ParamContext _localctx = new ParamContext(_ctx, getState());
		enterRule(_localctx, 4, RULE_param);
		try {
			_localctx = new ACLparamContext(_localctx);
			enterOuterAlt(_localctx, 1);
			{
			setState(20);
			match(COLON);
			setState(21);
			match(SYMBOL);
			setState(22);
			value();
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	@SuppressWarnings("CheckReturnValue")
	public static class ValueContext extends ParserRuleContext {
		public ValueContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_value; }
	 
		public ValueContext() { }
		public void copyFrom(ValueContext ctx) {
			super.copyFrom(ctx);
		}
	}
	@SuppressWarnings("CheckReturnValue")
	public static class ListValueContext extends ValueContext {
		public TerminalNode LPAREN() { return getToken(ACLParser.LPAREN, 0); }
		public TerminalNode RPAREN() { return getToken(ACLParser.RPAREN, 0); }
		public List<ValueContext> value() {
			return getRuleContexts(ValueContext.class);
		}
		public ValueContext value(int i) {
			return getRuleContext(ValueContext.class,i);
		}
		public ListValueContext(ValueContext ctx) { copyFrom(ctx); }
	}
	@SuppressWarnings("CheckReturnValue")
	public static class StringContext extends ValueContext {
		public TerminalNode STRING() { return getToken(ACLParser.STRING, 0); }
		public StringContext(ValueContext ctx) { copyFrom(ctx); }
	}
	@SuppressWarnings("CheckReturnValue")
	public static class AtomContext extends ValueContext {
		public TerminalNode SYMBOL() { return getToken(ACLParser.SYMBOL, 0); }
		public AtomContext(ValueContext ctx) { copyFrom(ctx); }
	}
	@SuppressWarnings("CheckReturnValue")
	public static class NestedMessageContext extends ValueContext {
		public MessageContext message() {
			return getRuleContext(MessageContext.class,0);
		}
		public NestedMessageContext(ValueContext ctx) { copyFrom(ctx); }
	}

	public final ValueContext value() throws RecognitionException {
		ValueContext _localctx = new ValueContext(_ctx, getState());
		enterRule(_localctx, 6, RULE_value);
		int _la;
		try {
			setState(35);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,2,_ctx) ) {
			case 1:
				_localctx = new AtomContext(_localctx);
				enterOuterAlt(_localctx, 1);
				{
				setState(24);
				match(SYMBOL);
				}
				break;
			case 2:
				_localctx = new StringContext(_localctx);
				enterOuterAlt(_localctx, 2);
				{
				setState(25);
				match(STRING);
				}
				break;
			case 3:
				_localctx = new NestedMessageContext(_localctx);
				enterOuterAlt(_localctx, 3);
				{
				setState(26);
				message();
				}
				break;
			case 4:
				_localctx = new ListValueContext(_localctx);
				enterOuterAlt(_localctx, 4);
				{
				setState(27);
				match(LPAREN);
				setState(29); 
				_errHandler.sync(this);
				_la = _input.LA(1);
				do {
					{
					{
					setState(28);
					value();
					}
					}
					setState(31); 
					_errHandler.sync(this);
					_la = _input.LA(1);
				} while ( (((_la) & ~0x3f) == 0 && ((1L << _la) & 50L) != 0) );
				setState(33);
				match(RPAREN);
				}
				break;
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static final String _serializedATN =
		"\u0004\u0001\u0006&\u0002\u0000\u0007\u0000\u0002\u0001\u0007\u0001\u0002"+
		"\u0002\u0007\u0002\u0002\u0003\u0007\u0003\u0001\u0000\u0001\u0000\u0001"+
		"\u0000\u0005\u0000\f\b\u0000\n\u0000\f\u0000\u000f\t\u0000\u0001\u0000"+
		"\u0001\u0000\u0001\u0001\u0001\u0001\u0001\u0002\u0001\u0002\u0001\u0002"+
		"\u0001\u0002\u0001\u0003\u0001\u0003\u0001\u0003\u0001\u0003\u0001\u0003"+
		"\u0004\u0003\u001e\b\u0003\u000b\u0003\f\u0003\u001f\u0001\u0003\u0001"+
		"\u0003\u0003\u0003$\b\u0003\u0001\u0003\u0000\u0000\u0004\u0000\u0002"+
		"\u0004\u0006\u0000\u0000&\u0000\b\u0001\u0000\u0000\u0000\u0002\u0012"+
		"\u0001\u0000\u0000\u0000\u0004\u0014\u0001\u0000\u0000\u0000\u0006#\u0001"+
		"\u0000\u0000\u0000\b\t\u0005\u0001\u0000\u0000\t\r\u0003\u0002\u0001\u0000"+
		"\n\f\u0003\u0004\u0002\u0000\u000b\n\u0001\u0000\u0000\u0000\f\u000f\u0001"+
		"\u0000\u0000\u0000\r\u000b\u0001\u0000\u0000\u0000\r\u000e\u0001\u0000"+
		"\u0000\u0000\u000e\u0010\u0001\u0000\u0000\u0000\u000f\r\u0001\u0000\u0000"+
		"\u0000\u0010\u0011\u0005\u0002\u0000\u0000\u0011\u0001\u0001\u0000\u0000"+
		"\u0000\u0012\u0013\u0005\u0005\u0000\u0000\u0013\u0003\u0001\u0000\u0000"+
		"\u0000\u0014\u0015\u0005\u0003\u0000\u0000\u0015\u0016\u0005\u0005\u0000"+
		"\u0000\u0016\u0017\u0003\u0006\u0003\u0000\u0017\u0005\u0001\u0000\u0000"+
		"\u0000\u0018$\u0005\u0005\u0000\u0000\u0019$\u0005\u0004\u0000\u0000\u001a"+
		"$\u0003\u0000\u0000\u0000\u001b\u001d\u0005\u0001\u0000\u0000\u001c\u001e"+
		"\u0003\u0006\u0003\u0000\u001d\u001c\u0001\u0000\u0000\u0000\u001e\u001f"+
		"\u0001\u0000\u0000\u0000\u001f\u001d\u0001\u0000\u0000\u0000\u001f \u0001"+
		"\u0000\u0000\u0000 !\u0001\u0000\u0000\u0000!\"\u0005\u0002\u0000\u0000"+
		"\"$\u0001\u0000\u0000\u0000#\u0018\u0001\u0000\u0000\u0000#\u0019\u0001"+
		"\u0000\u0000\u0000#\u001a\u0001\u0000\u0000\u0000#\u001b\u0001\u0000\u0000"+
		"\u0000$\u0007\u0001\u0000\u0000\u0000\u0003\r\u001f#";
	public static final ATN _ATN =
		new ATNDeserializer().deserialize(_serializedATN.toCharArray());
	static {
		_decisionToDFA = new DFA[_ATN.getNumberOfDecisions()];
		for (int i = 0; i < _ATN.getNumberOfDecisions(); i++) {
			_decisionToDFA[i] = new DFA(_ATN.getDecisionState(i), i);
		}
	}
}