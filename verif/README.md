# Verificação

O fluxo com Icarus Verilog, que não precisa do ModelSim nem da biblioteca `altera_mf`, está na raiz: [`sim/run_icarus.sh`](../sim/run_icarus.sh). O programa abaixo é o que está gravado em [`instruction.mif`](../instruction.mif).

# 📝 Como Inicializar a Memória de Instruções

1. Crie um arquivo chamado `instructions.txt` no mesmo diretório do script [`assembler.py`](assembler.py).

2. Escreva as instruções que deseja incluir na memória de instruções no arquivo, com cada instrução em uma linha separada.
    - As instruções devem ser escritas em assembly RISC-V. Consulte o arquivo [`assembler.py`](assembler.py) para verificar os formatos suportados.

3. Abra o terminal e execute o seguinte comando:
    ```shell
    python3 assembler.py
    ```

4. Se tudo estiver correto, um arquivo chamado `instruction.mif` será gerado no mesmo diretório do script.

# 🧪 Como Testar seu Programa com o Testbench

1. Crie um novo projeto no ModelSim.

2. Adicione todos os arquivos da pasta de design ao projeto.

3. Inclua o arquivo de testbench [`tb_top.sv`](tb_top.sv) no projeto.

4. No diretório do projeto, verifique se você possui os seguintes arquivos:
    - [compile_verilog](compile_verilog)
    - [runtb_top](runtb_top)
    - instruction.mif
    - data.mif

   Ajuste os caminhos dos arquivos nos scripts conforme necessário.

5. No terminal do ModelSim, execute o seguinte comando:
    ```shell
    do runtb_top
    ```

6. O processo de compilação e simulação será iniciado, e os resultados serão exibidos no terminal.
