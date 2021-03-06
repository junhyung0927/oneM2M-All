??    V      ?     |      x  ?   y  ,   t  5   ?  N   ?  7   &	  \   ^	  _   ?	  `   
  u   |
  i   ?
  b   \  V   ?  ?     D   ?  %   ?          (  5   B  B   x     ?  w   ?     P     g     ?     ?  $   ?     ?     ?     
          #     4     =     \  #   j     ?     ?     ?     ?     ?     ?     ?  H   ?     G     a  !   ?     ?     ?     ?     ?  #   ?     !     ;  $   [     ?     ?  #   ?  2   ?           $     E     c     ?  *   ?  *   ?     ?            #   )  #   M  &   q     ?     ?  ,   ?     ?       -   !     O     ^     m     ?     ?     ?     ?     ?  ?  ?  :  ?  5   ,  8   b  z   ?  <     a   S  ?   ?  _   =  |   ?  ?     `   ?  ]     ?   z  >   	  '   H     p      ?  ?   ?  O   ?     :  ?   U     ?     ?          0  &   C     j     ?     ?     ?     ?     ?  -   ?        (      &   <      c      l      u      ?      ?      ?   S   ?   "   1!  %   T!  -   z!     ?!     ?!     ?!  (   ?!  -   !"     O"  #   k"  .   ?"  *   ?"     ?"  '   #  -   /#     ]#  8   q#     ?#     ?#     ?#  5   ?#  ,   1$  "   ^$     ?$     ?$  B   ?$  B   ?$  E   4%     z%  -   ?%  ;   ?%  %   ?%     $&  6   @&     w&     ?&     ?&  !   ?&     ?&     ?&     '  )   :'        T   =          	   1          H      7      D   (                 L       
   /   F   M           ?   G       '   <                     @      5   R      .   C                 B                     9                  :       "          !   K   4               N   0               -       U             A   *             P                      S   8       )       V   I   2          &   #          J   %   6   ;           Q   $   +   ,       E   >      3          O          
If no -e, --expression, -f, or --file option is given, then the first
non-option argument is taken as the sed script to interpret.  All
remaining arguments are names of input files; if no input files are
specified, then the standard input is read.

       --help     display this help and exit
       --version  output version information and exit
   --follow-symlinks
                 follow symlinks when processing in place
   --posix
                 disable all GNU extensions.
   -R, --regexp-perl
                 use Perl 5's regular expressions syntax in the script.
   -b, --binary
                 open files in binary mode (CR+LFs are not processed specially)
   -e script, --expression=script
                 add the script to the commands to be executed
   -f script-file, --file=script-file
                 add the contents of script-file to the commands to be executed
   -i[SUFFIX], --in-place[=SUFFIX]
                 edit files in place (makes backup if SUFFIX supplied)
   -l N, --line-length=N
                 specify the desired line-wrap length for the `l' command
   -n, --quiet, --silent
                 suppress automatic printing of pattern space
   -u, --unbuffered
                 load minimal amounts of data from the input files and flush
                 the output buffers more often
   -z, --null-data
                 separate lines by NUL characters
 %s: -e expression #%lu, char %lu: %s
 %s: can't read %s: %s
 %s: file %s line %lu: %s
 %s: warning: failed to get security context of %s: %s %s: warning: failed to set default file creation context to %s: %s : doesn't want any addresses GNU sed home page: <http://www.gnu.org/software/sed/>.
General help using GNU software: <http://www.gnu.org/gethelp/>.
 Invalid back reference Invalid character class name Invalid collation character Invalid content of \{\} Invalid preceding regular expression Invalid range end Invalid regular expression Jay Fenlason Ken Pizzini Memory exhausted No match No previous regular expression Paolo Bonzini Premature end of regular expression Regular expression too big Success Tom Lord Trailing backslash Unmatched ( or \( Unmatched ) or \) Unmatched \{ Usage: %s [OPTION]... {script-only-if-no-other-script} [input-file]...

 `e' command not supported `}' doesn't want any addresses can't find label for jump to `%s' cannot remove %s: %s cannot rename %s: %s cannot stat %s: %s command only uses one address comments don't accept any addresses couldn't attach to %s: %s couldn't edit %s: is a terminal couldn't edit %s: not a regular file couldn't follow symlink %s: %s couldn't open file %s: %s couldn't open temporary file %s: %s delimiter character is not a single-byte character error in subprocess expected \ after `a', `c' or `i' expected newer version of sed extra characters after command incomplete command invalid reference \%d on `s' command's RHS invalid usage of +N or ~N as first address invalid usage of line address 0 missing command multiple `!'s multiple `g' options to `s' command multiple `p' options to `s' command multiple number options to `s' command no input files no previous regular expression number option to `s' command may not be zero option `e' not supported read error on %s: %s strings for `y' command are different lengths unexpected `,' unexpected `}' unknown command: `%c' unknown option to `s' unmatched `{' unterminated `s' command unterminated `y' command unterminated address regex Project-Id-Version: sed 4.2.2
Report-Msgid-Bugs-To: bug-gnu-utils@gnu.org
POT-Creation-Date: 2017-02-03 17:17-0800
PO-Revision-Date: 2016-06-19 20:26+02:00
Last-Translator: Petr Pisar <petr.pisar@atlas.cz>
Language-Team: Czech <translation-team-cs@lists.sourceforge.net>
Language: cs
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
X-Bugs: Report translation errors to the Language-Team address.
Plural-Forms: nplurals=3; plural=(n==1) ? 0 : (n>=2 && n<=4) ? 1 : 2;
 
Ne-li zadán žádný z přepínačů -e, --expression, -f nebo --file, pak první
argument, který není přepínačem, je považován za sedový skript a bude
vykonán. Všechny zbývající argumenty jsou jména vstupních souborů. Nejsou-li
zadány žádné vstupní soubory, bude čten standardní vstup.

       --help     zobrazí tuto nápovědu a skončí
       --version  vypíše informace o verzi a skončí
   --follow-symlinks
                 následuje symbolické odkazy, když zapisuje do vstupního
                 souboru
   --posix
                 vypne všechna GNU rozšíření
   -R, --regexp-perl
                 použije syntaxi regulárních výrazů podle Perlu verze 5
   -b, --binary
                 otevře soubory v binárním režimu (znaky CR+LF nejsou
                 zpracovávány zvláštně)
   -e script, --expression=SKRIPT
                 přidá skript mezi příkazy k provedení
   -f script-file, --file=SKRIPTOVÝ_SOUBOR
                 přidá obsah SKRIPTOVÉHO_SOUBORU mezi příkazy k provedení
   -i[PŘÍPONA], --in-place[=PŘÍPONA]
                 upravuje přímo vstupní soubory (vytváří zálohy, pokud je
                 poskytnuta PŘÍPONA)
   -l N, --line-length=N
                 určuje délku zarovnání řádku u příkazu „l“
   -n, --quiet, --silent
                 potlačí automatické vypisování prostoru vzorů
   -u, --unbuffered
                 čte co nejméně dat ze vstupních souborů a výstupní
                 buffery vyprazdňuje častěji
   -z, --null-data
                 oddělí řádky znaky NUL
 %s: -e výraz č. %'lu, znak %'lu: %s
 %s: %s nelze číst: %s
 %s: soubor %s, řádek %'lu: %s
 %s: pozor: nepodařilo se získat bezpečnostní kontext %s: %s %s: pozor: nastavení výchozího kontextu pro tvorbu souboru na %s selhalo: %s : nechce jakoukoliv adresu Domovská stránka GNU sed: <http://www.gnu.org/software/sed/>.
Obecný návod jak používat software GNU: <http://www.gnu.org/gethelp/>.
 Chybný zpětný odkaz Chybný název třídu znaků Chybný srovnávací znak Chybný obsah \{\} Chybný předešlý regulární výraz Chybný konec rozsahu Chybný regulární výraz Jay Fenlason Ken Pizzini Paměť vyčerpána Žádná shoda Žádný předcházející regulární výraz Paolo Bonzini Předčasný konec regulárního výrazu Regulární výraz je příliš velký Úspěch Tom Lord Zpětné lomítko na konci Neodpovídající ( nebo \( Neodpovídající ) nebo \) Neodpovídající \{ Použití: %s [PŘEPÍNAČ]… {SKRIPT_JEN_KDYŽ_JE_JEDINÝ} [VSTUPNÍ_SOUBOR]…

 příkaz „e“ není podporován „}“ nevyžaduje jakoukoliv adresu návěští pro skok na „%s“ nelze najít %s nelze odstranit: %s %s nelze přejmenovat: %s o %s nelze získat údaje: %s příkaz používá pouze jedinou adresu komentáře nepřipouštějí žádnou adresu do %s nelze připisovat: %s %s nelze upravovat: je to terminál %s nelze upravovat: není obyčejným souborem symbolický odkaz %s nelze následovat: %s soubor %s nelze otevřít: %s dočasný soubor %s nelze otevřít: %s oddělovací znak není jednobajtovým znakem chyba v podprocesu po „a“, „c“ nebo „i“ je očekávané „\“ očekávána nová verze sedu nadbytečné znaky po příkazu neúplný příkaz chybný odkaz \%d na pravé straně příkazu „s“ +N nebo ~N nelze použít jako první adresu chybné použití adresy řádku 0 chybějící příkaz vícenásobný „!“ vícenásobné použití přepínače „g“ s příkazem „s“ vícenásobné použití přepínače „p“ s příkazem „s“ příkaz „s“ může mít maximálně jednu číselný přepínač žádné vstupní soubory žádný předcházející regulární výraz číselný přepínač příkazu „s“ nemůže být nula přepínač „e“ není podporován chyba při čtení z %s: %s řetězce pro příkaz „y“ mají rozdílnou délku neočekávaná „,“ neočekávaná „}“ neznámý příkaz: „%c“ neznámý přepínač pro „s“ neodpovídající „{“ neukončený příkaz „s“ neukončený příkaz „y“ neukončená adresa regulárního výrazu 