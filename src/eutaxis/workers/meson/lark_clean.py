# This file is part of https://github.com/KurtBoehm/eutaxis.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from collections.abc import Iterator
from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory
from typing import override

from colorama import Fore
from lark import Lark, Token, Transformer, Tree
from lark.lark import PostLex
from lark.reconstruct import Reconstructor
from lark.tree import Branch


class StripNewlineInParens(PostLex):
    """
    Post-lexer that removes ``NEWLINE`` tokens inside ``()``, ``[]``, ``{}`` while
    preserving preceding newlines for comments.

    This keeps logical lines within parentheses contiguous for parsing, but still
    attaches the suppressed newline text to following comments so reconstruction can
    reproduce the original layout.
    """

    def __init__(self) -> None:
        """
        Initialize the post-lexer.

        ``level`` tracks the nesting depth of ``()``, ``[]``, and ``{}``, and
        ``prev_nl`` stores a pending newline that should be attached to the next
        comment token.
        """
        self.level: int = 0
        self.prev_nl: str | None = None

    @override
    def process(self, stream: Iterator[Token]) -> Iterator[Token]:
        """
        Process a token stream, stripping ``NEWLINE`` tokens inside parentheses.

        Newlines within any of ``()``, ``[]``, or ``{}`` are removed from the token
        stream but their text is prepended to the next ``COMMENT`` token, if any.

        :param stream: Input token stream from the lexer.
        :return: A new token stream with adjusted newlines and comments.
        """
        for token in stream:
            # Track opening/closing delimiters
            if token.type in {"LPAR", "LBRACKET", "LBRACE"}:
                self.level += 1
                self.prev_nl = None
                yield token
            elif token.type in {"RPAR", "RBRACKET", "RBRACE"}:
                self.level -= 1
                self.prev_nl = None
                yield token
            elif token.type == "NEWLINE" and self.level > 0:
                self.prev_nl = token.value
                # Inside any (), [], {}, ignore NEWLINE completely
                continue
            elif token.type == "COMMENT":
                if self.prev_nl:
                    # Add the preceding newline to comments
                    yield Token("COMMENT", f"{self.prev_nl}{token.value}")
                else:
                    yield token
                self.prev_nl = None
            else:
                self.prev_nl = None
                yield token


def filter_branches(children: list[Branch[Token]]) -> list[Branch[Token]]:
    """
    Filter out ``COMMENT`` and ``NEWLINE`` tokens from a branch list.

    This is used to operate on the syntactic structure without whitespace or comments
    interfering with argument analysis.

    :param children: Branch nodes and tokens to be filtered.
    :return: Children with ``COMMENT`` and ``NEWLINE`` tokens removed.
    """
    return [
        c
        for c in children
        if not (isinstance(c, Token) and c.type in {"COMMENT", "NEWLINE"})
    ]


# Function name → preferred keyword argument order.
_library_order = [
    "sources",
    "include_directories",
    "dependencies",
    "link_with",
    "link_whole",
    "link_args",
    "override_options",
    "pic",
    "c_args",
    "cpp_args",
    "fortran_args",
    "gnu_symbol_visibility",
    "build_by_default",
    "install",
    "version",
    "soversion",
]
_kwargs_order: dict[str, list[str]] = {
    "compiles": ["name", "args", "dependencies"],
    "configure_file": [
        "input",
        "output",
        "configuration",
        "format",
        "command",
        "copy",
        "build_subdir",
    ],
    "custom_target": [
        "input",
        "output",
        "command",
        "build_by_default",
        "install",
        "install_dir",
    ],
    "declare_dependency": [
        "sources",
        "include_directories",
        "dependencies",
        "link_with",
        "link_args",
        "compile_args",
        "version",
    ],
    "dependency": ["language", "required"],
    "executable": [
        "include_directories",
        "dependencies",
        "c_args",
        "cpp_args",
        "fortran_args",
    ],
    "library": _library_order,
    "shared_library": _library_order,
    "static_library": _library_order,
    "subproject": ["default_options", "required"],
    "run_target": [],
    "run_command": [],
}


def _kwarg_kw(kwarg: Tree[Token]) -> str:
    """
    Extract the keyword name from a ``keyword_argument`` tree node.

    :param kwarg: A ``keyword_argument`` node from the parse tree.
    :return: The keyword name.
    """
    kw = kwarg.children[0]
    assert isinstance(kw, Token)
    value = kw.value
    assert isinstance(value, str)
    return value


class ArgumentSorter(Transformer[Token, Tree[Token]]):
    """
    Lark transformer that normalizes keyword argument ordering for selected Meson
    functions and methods.

    Keyword argument ordering is controlled by :data:`_kwargs_order`.

    * Positional arguments are preserved in their original order.
    * Positional arguments must precede all keyword arguments.
    * If a function is not listed in :data:`_kwargs_order`, its arguments are left
      unchanged.
    """

    def _handle_function(
        self,
        data: str,
        children: list[Branch[Token]],
        *,
        verbose: bool = False,
    ) -> Tree[Token]:
        """
        Common handler for function and method calls with an ``argument_list``.

        If the callee name is configured in :data:`_kwargs_order`, the
        ``keyword_argument`` children of the ``argument_list`` are reordered to match
        the configured order. Otherwise the original tree is returned unmodified.

        :param data: Tree label to use for the returned node (e.g. ``"function_expression"``).
        :param children: Original children of the call expression node.
        :param verbose: If ``True``, debug information is printed to ``stdout``.
        :return: Either the original tree or a new tree with reordered arguments.
        """
        identity = Tree(data, children)
        children = filter_branches(children)

        if len(children) == 1:
            return identity
        assert len(children) == 2, children

        name, args = children
        assert isinstance(name, Token)
        assert isinstance(args, Tree) and args.data == "argument_list"

        achildren = filter_branches(args.children)
        trailing_comma = achildren[-1] == Token("COMMA", ",")
        if verbose:
            print(
                name,
                [c.data if isinstance(c, Tree) else c for c in achildren],
                trailing_comma,
            )

        positional_args: list[Tree[Token]] = []
        keyword_args: list[Tree[Token]] = []
        for child in achildren:
            match child:
                case Token("COMMA", ","):
                    pass
                case Tree("positional_argument", [_]):
                    assert not keyword_args, "positional arguments before kwargs!"
                    positional_args.append(child)
                case Tree("keyword_argument", [_, _]):
                    keyword_args.append(child)
                case _:
                    raise RuntimeError(f"Unknown argument: {child!r}")

        order = _kwargs_order.get(name)
        if order is None:
            return identity
        try:
            sorted_keyword_args = sorted(
                keyword_args,
                key=lambda t: order.index(_kwarg_kw(t)),
            )
        except ValueError:
            print(name, [_kwarg_kw(t) for t in keyword_args], order)
            raise

        if keyword_args == sorted_keyword_args:
            return identity

        sorted_children: list[Branch[Token]] = []
        for c in positional_args + sorted_keyword_args:
            sorted_children.append(c)
            sorted_children.append(Token("COMMA", ","))
        sorted_children.pop()

        return Tree(data, [name, Tree("argument_list", sorted_children)])

    def function_expression(self, children: list[Branch[Token]]) -> Tree[Token]:
        """
        Transform a free function call and sort its keyword arguments if applicable.

        This is invoked for parse nodes with ``data == "function_expression"``.
        """
        return self._handle_function("function_expression", children, verbose=False)

    def method_postfix(self, children: list[Branch[Token]]) -> Tree[Token]:
        """
        Transform a method call (postfix form) and sort its keyword arguments if
        applicable.

        This is invoked for parse nodes with ``data == "method_postfix"``.
        """
        return self._handle_function("method_postfix", children, verbose=False)


def lark_clean(
    src_paths: list[Path],
    *,
    config: Path | None = None,
    in_place: bool = True,
    format: bool = True,
) -> None:
    from importlib import resources

    from . import __name__ as pkg_name

    """
    Clean-up Meson files using a Lark grammar.

    For each given Meson build file:

    * Parse it with the Meson grammar.
    * Reorder keyword arguments in known functions and methods.
    * Reconstruct the source code.
    * Optionally run ``muon fmt`` on the result.
    * Write back in place or print to ``stdout``.

    :param src_paths: Meson build files to process.
    :param config: Optional muon configuration file.
    :param in_place: Rewrite the input files in place instead of printing to ``stdout``.
    :param format: Enable ``muon fmt`` post-processing.
    """
    lark_resource = resources.files(pkg_name) / "meson.lark"
    meson_grammar = lark_resource.read_text(encoding="utf-8")

    parser = Lark(
        meson_grammar,
        start="build_definition",
        parser="lalr",
        lexer="basic",
        postlex=StripNewlineInParens(),
        propagate_positions=True,
        maybe_placeholders=False,
    )

    for src_path in src_paths:
        print(src_path)
        code = src_path.read_text(encoding="utf-8")
        tree = parser.parse(code)

        trans = ArgumentSorter().transform(tree)

        recon = Reconstructor(parser).reconstruct(trans)

        if format:
            with TemporaryDirectory() as tmp:
                tmp_file = Path(tmp) / "meson.build"
                tmp_file.write_text(recon)
                cmd = [
                    "muon",
                    "fmt",
                    *(["-c", config] if config else []),
                    "-i",
                    tmp_file,
                ]
                run(cmd, check=True)

                dst = tmp_file.read_text()
                if in_place:
                    if code != dst:
                        src_path.write_text(dst)
                    else:
                        print(f"{Fore.GREEN}{src_path} remains unchanged!{Fore.RESET}")
                else:
                    print(dst, end="")
        else:
            print(recon)
