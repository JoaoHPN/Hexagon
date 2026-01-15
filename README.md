Hexagon

Hexagon é um dashboard de Business Intelligence desenvolvido em Python com Streamlit, focado na análise de vendas nos Estados Unidos.
O projeto permite explorar dados de vendas por estado, produto, loja e vendedor, com visualizações interativas e filtros dinâmicos, incluindo comportamento de cross-filter inspirado no Power BI.

Funcionalidades
Mapa interativo dos EUA com estados destacados dinamicamente
Filtros por estado e produto
KPIs de vendas consolidadas
Gráficos de barras e linhas (Plotly)
Ranking dos Top 10 vendedores e Top 10 lojas
Cross-filter interativo por clique nas lojas
Arquitetura modular (components, data layer e queries SQL)

Funcionamento dos filtros e responsividade
O dashboard possui filtros dinâmicos que controlam todos os elementos visuais da aplicação.
Os filtros de estado e produto permitem restringir o conjunto de dados exibido no mapa, nas tabelas e nos gráficos, garantindo consistência entre todas as visualizações.
O mapa dos Estados Unidos reage automaticamente às seleções feitas nos filtros, destacando visualmente apenas os estados ativos.
Nos gráficos de Melhores Lojas, o clique em uma ou mais lojas funciona como um filtro adicional. Essa seleção é acumulativa e afeta todos os outros gráficos, tabelas e indicadores do dashboard, permitindo análises exploratórias semelhantes ao comportamento de ferramentas como o Power BI.
Todas as visualizações são recalculadas automaticamente a cada interação, mantendo sincronização total entre filtros, gráficos e indicadores.

Tecnologias utilizadas
Python 3.11+
Streamlit
Plotly
Pandas
SQL Server (AdventureWorks)
Git e GitHub

Como executar o projeto
Clone o repositório:
git clone https://github.com/JoaoHPN/Hexagon.git

Execute o app:
python -m streamlit run app.py

O dashboard será aberto em:
http://localhost:8501

Estrutura do projeto
Exagon/
├─ app.py
├─ db.py
├─ data_layer.py
├─ components/
│ ├─ filters_view.py
│ ├─ map_view.py
│ ├─ charts_view.py
│ └─ sellers_stores_view.py

Observações
O projeto utiliza cache do Streamlit para otimização de performance.
A conexão com o banco de dados foi configurada para evitar bloqueios no SQL Server (MARS).
